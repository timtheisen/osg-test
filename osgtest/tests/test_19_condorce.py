import cagen
import re
import os

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.condor as condor
import osgtest.library.service as service

class TestStartCondorCE(osgunittest.OSGTestCase):
    # Tests 01-02 are needed to reconfigure condor to work with HTCondor-CE
    def test_01_configure_condor(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client')

        core.config['condor-ce.condor-cfg'] = '/etc/condor/config.d/99-osgtest.condor.conf'
        contents = """SCHEDD_INTERVAL=1
QUEUE_SUPER_USER_MAY_IMPERSONATE = .*"""

        files.write(core.config['condor-ce.condor-cfg'],
                    contents,
                    owner='condor-ce',
                    chmod=0644)

    def test_02_reconfigure_condor(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client')
        self.skip_bad_unless(core.state['condor.running-service'], 'Condor not running')

        # Ensure that the Condor master is available for reconfig
        self.failUnless(condor.wait_for_daemon(core.config['condor.collectorlog'],
                                               core.config['condor.collectorlog_stat'],
                                               'Master',
                                               300.0),
                        'Condor Master not available for reconfig')

        command = ('condor_reconfig', '-debug')
        core.check_system(command, 'Reconfigure Condor')
        self.assert_(service.is_running('condor'), 'Condor not running after reconfig')

    def test_03_configure_auth(self):
        if core.osg_release() < 3.4:
            return

        core.skip_ok_unless_installed('htcondor-ce', 'lcmaps-plugins-voms')
        core.config['condorce.env'] = os.path.join('/etc', 'sysconfig', 'condor-ce')
        files.append(core.config['condorce.env'],
                     '''export LLGT_VOMS_ENABLE_CREDENTIAL_CHECK=1
export LCMAPS_DEBUG_LEVEL=5''',
                     owner='condorce')

    def test_04_configure_ce(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client')

        # Set up Condor, PBS, and Slurm routes
        # Leave the GRIDMAP knob in tact to verify that it works with the LCMAPS VOMS plugin
        core.config['condor-ce.condor-ce-cfg'] = '/etc/condor-ce/config.d/99-osgtest.condor-ce.conf'
        condor_contents = """GRIDMAP = /etc/grid-security/grid-mapfile
ALL_DEBUG=D_FULLDEBUG
JOB_ROUTER_DEFAULTS = $(JOB_ROUTER_DEFAULTS) [set_default_maxMemory = 128;]
JOB_ROUTER_ENTRIES = \\
   [ \\
     GridResource = "batch pbs"; \\
     TargetUniverse = 9; \\
     name = "Local_PBS"; \\
     Requirements = target.osgTestBatchSystem =?= "pbs"; \\
   ] \\
   [ \\
     GridResource = "batch slurm"; \\
     TargetUniverse = 9; \\
     name = "Local_Slurm"; \\
     Requirements = target.osgTestBatchSystem =?= "slurm"; \\
   ] \\
   [ \\
     TargetUniverse = 5; \\
     name = "Local_Condor"; \\
     Requirements = (target.osgTestBatchSystem =!= "pbs" && target.osgTestBatchSystem =!= "slurm"); \\
   ]

JOB_ROUTER_SCHEDD2_SPOOL=/var/lib/condor/spool
JOB_ROUTER_SCHEDD2_NAME=$(FULL_HOSTNAME)
JOB_ROUTER_SCHEDD2_POOL=$(FULL_HOSTNAME):9618
"""

        if core.rpm_is_installed('htcondor-ce-view'):
            condor_contents += "\nDAEMON_LIST = $(DAEMON_LIST), CEVIEW, GANGLIAD, SCHEDD"
            core.config['condor-ce.view-port'] = condor.ce_config_val('HTCONDORCE_VIEW_PORT')

        files.write(core.config['condor-ce.condor-ce-cfg'],
                    condor_contents,
                    owner='condor-ce',
                    chmod=0644)

        # Add host DN to condor_mapfile
        if core.options.hostcert:
            core.config['condor-ce.condorce_mapfile'] = '/etc/condor-ce/condor_mapfile'
            hostcert_dn, _ = cagen.certificate_info(core.config['certs.hostcert'])
            mapfile_contents = files.read('/etc/condor-ce/condor_mapfile')
            mapfile_contents.insert(0, re.sub(r'([/=\.])', r'\\\1', "GSI \"^%s$\" " % hostcert_dn) + \
                                              "%s@daemon.opensciencegrid.org\n" % core.get_hostname())
            files.write(core.config['condor-ce.condorce_mapfile'],
                        mapfile_contents,
                        owner='condor-ce',
                        chmod=0644)

    def test_05_start_condorce(self):
        if core.el_release() >= 7:
            core.config['condor-ce.lockfile'] = '/var/lock/condor-ce/htcondor-ceLock'
        else:
            core.config['condor-ce.lockfile'] = '/var/lock/subsys/condor-ce'
        core.state['condor-ce.started-service'] = False
        core.state['condor-ce.schedd-ready'] = False

        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client')
        core.config['condor-ce.collectorlog'] = condor.ce_config_val('COLLECTOR_LOG')

        if service.is_running('condor-ce'):
            # Required to accept changes to the mapfile, which caused
            # issues in the nightly due to bad htcondor-ce-2.0.8-2
            # packaging remove after OSG 3.3.17. We don't use service.stop()
            # because it only stops services that we've started
            if core.el_release() < 7:
                command = ('service', 'condor-ce', 'stop')
            else:
                command = ('systemctl', 'stop', 'condor-ce')
            core.check_system(command, 'Stop condor-ce service')
            service.check_start('condor-ce')
            core.state['condor-ce.schedd-ready'] = True
            self.skip_ok('already running')

        service.check_start('condor-ce')

        stat = core.get_stat(core.config['condor-ce.collectorlog'])
        if condor.wait_for_daemon(core.config['condor-ce.collectorlog'], stat, 'Schedd', 300.0):
            core.state['condor-ce.schedd-ready'] = True
