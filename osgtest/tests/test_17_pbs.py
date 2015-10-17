import os
import re
import time
from datetime import date

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStartPBS(osgunittest.OSGTestCase):

    pbs_config = """
create queue batch queue_type=execution
set queue batch started=true
set queue batch enabled=true
set queue batch resources_default.nodes=1
set queue batch resources_default.walltime=3600
set server default_queue=batch
set server keep_completed = 600
set server job_nanny = True
set server scheduling=true
set server acl_hosts += *
set server acl_host_enable = True
"""
    required_rpms = ['torque-mom',
                     'torque-server',
                     'torque-scheduler',
                     'torque-client', # for qmgr
                     'munge']


    def test_01_fix_spool_permissions(self):
        # EPEL's torque-mom-4.2.10-1 has broken permissions on a few directories:
        # https://bugzilla.redhat.com/show_bug.cgi?id=1216037
        core.skip_ok_unless_installed(*self.required_rpms)
        for bad_dir in ['checkpoint', 'spool', 'undelivered']:
            # Make the dirs owner/group/world writeable/readable/executable
            # and flip the sticky bit
            os.chmod('/var/lib/torque/' + bad_dir, 01777)

    def test_02_start_munge(self):
        if core.el_release() == 5:
            core.config['munge.lockfile'] = '/var/lock/subsys/munge'
        elif core.el_release() == 6:
            core.config['munge.lockfile'] = '/var/lock/subsys/munged'
        elif core.el_release() == 7:
            core.config['munge.lockfile'] = '/var/run/munge/munged.pid'
        core.config['munge.keyfile'] = '/etc/munge/munge.key'
        core.state['munge.running'] = False

        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(os.path.exists(core.config['munge.lockfile']), 'already running')

        files.preserve(core.config['munge.keyfile'], 'pbs')
        command = ('/usr/sbin/create-munge-key', '-f',)
        stdout, _, fail = core.check_system(command, 'Create munge key')
        self.assert_(stdout.find('error') == -1, fail)
        command = ('service', 'munge', 'start')
        stdout, _, fail = core.check_system(command, 'Start munge daemon')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['munge.lockfile']),
                     'munge lock file missing')
        core.state['munge.running'] = True

    def test_03_start_mom(self):
        core.config['torque.mom-lockfile'] = '/var/lock/subsys/pbs_mom'
        core.state['torque.pbs-mom-running'] = False

        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(os.path.exists(core.config['torque.mom-lockfile']), 'pbs mom apparently running')

        core.config['torque.mom-config'] = '/var/lib/torque/mom_priv/config'

        files.write(core.config['torque.mom-config'],
                    "$pbsserver %s\n" % core.get_hostname(),
                    owner='pbs')

        command = ('service', 'pbs_mom', 'start')
        stdout, _, fail = core.check_system(command, 'Start pbs mom daemon')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['torque.mom-lockfile']),
                     'PBS mom run lock file missing')
        core.state['torque.pbs-mom-running'] = True


    def test_04_start_pbs_sched(self):
        core.config['torque.sched-lockfile'] = '/var/lock/subsys/pbs_sched'
        core.state['torque.pbs-sched-running'] = False

        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(os.path.exists(core.config['torque.sched-lockfile']), 'pbs scheduler apparently running')

        command = ('service', 'pbs_sched', 'start')
        stdout, _, fail = core.check_system(command, 'Start pbs scheduler daemon')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['torque.sched-lockfile']),
                     'pbs sched run lock file missing')
        core.state['torque.pbs-sched-running'] = True

    def test_05_start_pbs(self):
        core.config['torque.pbs-lockfile'] = '/var/lock/subsys/pbs_server'
        core.state['torque.trqauthd-started'] = False
        core.state['torque.pbs-server-running'] = False
        core.state['torque.pbs-server-started'] = False
        core.state['torque.pbs-configured'] = False
        core.state['torque.nodes-up'] = False
        core.config['torque.pbs-nodes-file'] = '/var/lib/torque/server_priv/nodes'
        core.config['torque.pbs-servername-file'] = '/var/lib/torque/server_name'

        core.skip_ok_unless_installed(*self.required_rpms)
        if os.path.exists(core.config['torque.pbs-lockfile']):
            core.state['torque.pbs-server-running'] = True
            self.skip_ok('pbs server apparently running')

        # set hostname as servername instead of localhost
        files.write(core.config['torque.pbs-servername-file'],
                    "%s" % core.get_hostname(),
                    owner='pbs')
        core.state['torque.pbs-configured'] = True

        # PBS uses trqauthd for auth between clients and the server
        # In 4.2.10 the server doesn't start it or have a service for it
        # https://bugzilla.redhat.com/show_bug.cgi?id=1215207
        processes, _, _ = core.check_system(('ps', '-e'), 'checking if trqauthd already running')
        if not re.search(r'trqauthd', processes):
            command = ('/usr/sbin/trqauthd')
            core.check_system(command, 'Start trqauthd for pbs_server')
            core.state['torque.trqauthd-started'] = True

        if not os.path.exists('/var/lib/torque/server_priv/serverdb'):
                command = ('service', 'pbs_server', 'create') # this creates the default config and starts the service
                stdout, _, fail = core.check_system(command, 'create initial pbs serverdb config')
                self.assert_(stdout.find('error') == -1, fail)

        # This gets wiped if we write it before the initial 'service pbs_server create'
        # However, this file needs to be in place before the service is started so we 
        # restart the service after 'initial configuration'
        files.write(core.config['torque.pbs-nodes-file'], # add the local node as a compute node
                    "%s np=1\n" % core.get_hostname(),
                    owner='pbs')

        # Sometimes the restart command throws an error on stop but still manages 
        # to kill the service, meaning that the service doesn't get brought back up
        command = ('service', 'pbs_server', 'stop')
        core.system(command, 'stop pbs server daemon')

        server_log = '/var/log/torque/server_logs/' + date.today().strftime('%Y%m%d')
        try:
            server_log_stat = os.stat(server_log)
        except OSError:
            server_log_stat = None
            
        command = ('service', 'pbs_server', 'start')
        stdout, _, fail = core.check_system(command, 'Start pbs server daemon')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['torque.pbs-lockfile']),
                     'pbs server run lock file missing')
        core.state['torque.pbs-server-started'] = True
        core.state['torque.pbs-server-running'] = True

        # Wait until the server is up before writing the rest of the config
        core.monitor_file(server_log, server_log_stat, '.*Server Ready.*', 60.0)
        core.check_system("echo '%s' | qmgr %s" % (self.pbs_config, core.get_hostname()),
                          "Configuring pbs server",
                          shell=True)

        # wait up to 5 minutes for the server to recognize the node
        start_time = time.time()
        while ((time.time() - start_time) < 600):
            command = ('/usr/bin/qnodes', '-s', core.get_hostname())
            stdout, _, fail = core.check_system(command, 'Get pbs node info')
            self.assert_(stdout.find('error') == -1, fail)
            if stdout.find('state = free'):
                core.state['torque.nodes-up'] = True
                break
        if not core.state['torque.nodes-up']:
            self.fail('PBS nodes not coming up')

