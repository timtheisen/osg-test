import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import re
import time

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


    def test_01_start_munge(self):
        if core.el_release() == 5:
            core.config['munge.lockfile'] = '/var/lock/subsys/munge'
        elif core.el_release() == 6:
            core.config['munge.lockfile'] = '/var/lock/subsys/munged'
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

    def test_02_start_mom(self):
        core.config['torque.mom-lockfile'] = '/var/lock/subsys/pbs_mom'
        core.state['torque.pbs-mom-running'] = False
       
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(os.path.exists(core.config['torque.mom-lockfile']), 'pbs mom apparently running')

        if core.el_release() == 5:
            core.config['torque.mom-config'] = '/var/torque/mom_priv/config'
        elif core.el_release() == 6:
            core.config['torque.mom-config'] = '/var/lib/torque/mom_priv/config'
        else:
            self.skip_ok('Distribution version not supported')

        files.write(core.config['torque.mom-config'],
                    "$pbsserver %s\n" % core.get_hostname(),
                    owner='pbs')

        command = ('service', 'pbs_mom', 'start')
        stdout, _, fail = core.check_system(command, 'Start pbs mom daemon')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['torque.mom-lockfile']),
                     'PBS mom run lock file missing')
        core.state['torque.pbs-mom-running'] = True


    def test_03_start_pbs_sched(self):
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

    def test_04_start_pbs(self):
        core.config['torque.pbs-lockfile'] = '/var/lock/subsys/pbs_server'
        core.state['torque.pbs-server-running'] = False
        core.state['torque.pbs-configured'] = False
        core.state['torque.nodes-up'] = False
        if core.el_release() == 5:
            core.config['torque.pbs-nodes-file'] = '/var/torque/server_priv/nodes'
            core.config['torque.pbs-servername-file'] = '/var/torque/server_name'
        elif core.el_release() == 6:
            core.config['torque.pbs-nodes-file'] = '/var/lib/torque/server_priv/nodes'
            core.config['torque.pbs-servername-file'] = '/var/lib/torque/server_name'
        else:
            self.skip_ok('Distribution version not supported')

        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(os.path.exists(core.config['torque.pbs-lockfile']), 'pbs server apparently running')
    
        # add the local node as a compute node
        files.write(core.config['torque.pbs-nodes-file'],
                    "%s np=1\n" % core.get_hostname(),
                    owner='pbs')
        # set hostname as servername instead of localhost
        files.write(core.config['torque.pbs-servername-file'],
                    "%s" % core.get_hostname(),
                    owner='pbs')
        command = ('service', 'pbs_server', 'start')
        stdout, _, fail = core.check_system(command, 'Start pbs server daemon')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['torque.pbs-lockfile']),
                     'pbs server run lock file missing')
        core.state['torque.pbs-server'] = True
        core.state['torque.pbs-server-running'] = True

        core.check_system("echo '%s' | qmgr %s" % (self.pbs_config,
                                                   core.get_hostname()),
                          "Configuring pbs server",
                          shell = True)
        core.state['torque.pbs-configured'] = True

        # wait up to 5 minutes for the server to come up and trigger a failure
        # if that doesn't happen
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

