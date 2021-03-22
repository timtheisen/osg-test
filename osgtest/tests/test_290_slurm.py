import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.mysql as mysql
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

CLUSTER_NAME = 'osg_test'
CTLD_LOG = '/var/log/slurm/slurmctld.log'
SLURM_LOG = '/var/log/slurm/slurm.log'
SHORT_HOSTNAME = core.get_hostname().split('.')[0]

SLURMDBD_CONFIG = """AuthType=auth/munge
DbdHost=localhost
DebugLevel=debug5
LogFile=/var/log/slurm/slurmdbd.log
StorageType=accounting_storage/mysql
StorageLoc={name}
StorageUser={user}
StoragePass={password}
"""

SLURM_CONFIG = """AccountingStorageHost=localhost
AccountingStorageLoc=/tmp/slurm_job_accounting.txt
AccountingStorageType=accounting_storage/slurmdbd
AuthType=auth/munge
ClusterName={cluster}
ControlMachine={short_hostname}
JobAcctGatherType=jobacct_gather/linux
KillWait=30
NodeName={short_hostname} Procs=1 RealMemory=128 State=UNKNOWN
PartitionName=debug Nodes={short_hostname} Default=YES MaxTime=INFINITE State=UP
ReturnToService=2
SlurmctldDebug=debug5
SlurmctldTimeout=300
SlurmctldLogFile={ctld_log}
SlurmdLogFile=/var/log/slurm/slurm.log
SlurmdDebug=debug5
StateSaveLocation=/var/spool/slurmd
"""

SLURM_CGROUPS_CONFIG = """CgroupAutomount=yes
CgroupMountpoint=/cgroup
ConstrainCores=no
ConstrainRAMSpace=no
"""

SLURM_CGROUPS_DEVICE_CONFIG = """/dev/null
/dev/urandom
/dev/zero
/dev/sda*
/dev/cpu/*/*
/dev/pts/*
"""


class TestStartSlurm(osgunittest.OSGTestCase):

    def slurm_reqs(self):
        core.skip_ok_unless_installed(*core.SLURM_PACKAGES)
        self.skip_bad_unless(service.is_running('munge'), 'slurm requires munge')

    def test_01_slurm_config(self):
        self.slurm_reqs()
        core.config['slurm.config-dir'] = '/etc/slurm'
        core.config['slurm.config'] = os.path.join(core.config['slurm.config-dir'], 'slurm.conf')
        files.write(core.config['slurm.config'],
                    SLURM_CONFIG.format(short_hostname=SHORT_HOSTNAME,
                                        cluster=CLUSTER_NAME,
                                        ctld_log=CTLD_LOG),
                    owner='slurm',
                    chmod=0o644)
        core.config['cgroup.config'] = os.path.join(core.config['slurm.config-dir'], 'cgroup.conf')
        config = SLURM_CGROUPS_CONFIG
        if core.el_release() == 6:
            config += "\nCgroupMountpoint=/cgroup"
        files.write(core.config['cgroup.config'],
                    config,
                    owner='slurm',
                    chmod=0o644)

        core.config['cgroup_allowed_devices_file.conf'] = os.path.join(core.config['slurm.config-dir'],
                                                                       'cgroup_allowed_devices_file.conf')
        files.write(core.config['cgroup_allowed_devices_file.conf'],
                    SLURM_CGROUPS_DEVICE_CONFIG,
                    owner='slurm',
                    chmod=0o644)

    def test_02_start_slurmdbd(self):
        core.state['slurmdbd.started-service'] = False
        self.slurm_reqs()
        self.skip_bad_unless(mysql.is_running(), 'slurmdbd requires mysql')
        core.config['slurmdbd.config'] = os.path.join(core.config['slurm.config-dir'], 'slurmdbd.conf')
        core.config['slurmdbd.user'] = "'osg-test-slurm'@'localhost'"
        core.config['slurmdbd.name'] = "osg_test_slurmdb"

        mysql.check_execute("create database %s; " % core.config['slurmdbd.name'], 'create slurmdb')
        mysql.check_execute("create user %s; " % core.config['slurmdbd.user'], 'add slurmdb user')
        mysql.check_execute("grant usage on *.* to %s; " % core.config['slurmdbd.user'], 'slurmdb user access')
        mysql.check_execute("grant all privileges on %s.* to %s identified by '%s'; " % (core.config['slurmdbd.name'],
                                                                                         core.config['slurmdbd.user'],
                                                                                         core.options.password),
                            'slurmdb user permissions')
        mysql.check_execute("flush privileges;", 'reload privileges')

        files.write(core.config['slurmdbd.config'],
                    SLURMDBD_CONFIG.format(name=core.config['slurmdbd.name'],
                                           user=core.config['slurmdbd.user'].split('\'')[1],
                                           password=core.options.password,),
                    owner='slurm',
                    chmod=0o644)
        service.check_start('slurmdbd')

        # Adding the cluster to the database
        command = ('sacctmgr', '-i', 'add', 'cluster', CLUSTER_NAME)
        core.check_system(command, 'add slurm cluster')

    def test_03_start_slurm(self):
        core.config['slurm.service-name'] = 'slurm'
        if core.el_release() >= 7:
            core.config['slurm.service-name'] += 'd'
            core.config['slurm.ctld-service-name'] = 'slurmctld'
        core.state['%s.started-service' % core.config['slurm.service-name']] = False
        self.slurm_reqs()
        self.skip_ok_if(service.is_running(core.config['slurm.service-name']), 'slurm already running')

        stat = core.get_stat(CTLD_LOG)

        if core.el_release() >= 7:
            # slurmctld is handled by /etc/init.d/slurm on EL6
            command = ['slurmctld']
            core.check_system(command, 'enable slurmctld')
            service.check_start(core.config['slurm.service-name'])
            service.check_start(core.config['slurm.ctld-service-name'])
        else:
            service.check_start(core.config['slurm.service-name'])

        core.monitor_file(CTLD_LOG,
                          stat,
                          'slurm_rpc_node_registration complete for %s' % SHORT_HOSTNAME,
                          60.0)
        log_stat = core.get_stat(SLURM_LOG)
        core.monitor_file(SLURM_LOG,
                          log_stat,
                          'slurmd started',
                          60.0)
        command = ['scontrol', 'update', 'nodename=%s' % SHORT_HOSTNAME, 'state=idle']
        core.check_system(command, 'enable slurm node')
