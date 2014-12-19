import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import unittest

class TestStopPBS(osgunittest.OSGTestCase):

    required_rpms = ['torque-mom',
                     'torque-server',
                     'torque-scheduler',
                     'torque-client',
                     'munge']

    def test_01_stop_mom(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(core.state['torque.pbs-mom-running'] == False, 'did not start pbs mom server')
            
        command = ('service', 'pbs_mom', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop pbs mom')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(not os.path.exists(core.config['torque.mom-lockfile']),
                     'PBS mom run lock file still present')

        files.restore(core.config['torque.mom-config'], 'pbs')
        core.state['torque.pbs-mom-running'] = False

    def test_02_stop_server(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(core.state['torque.pbs-server-running'] == False, 'did not start pbs server')

        command = ('service', 'pbs_server', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop pbs server')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(not os.path.exists(core.config['torque.pbs-lockfile']),
                     'PBS server run lock file still present')

        files.restore(core.config['torque.pbs-servername-file'], 'pbs')
        core.state['torque.pbs-server-running'] = False
        core.state['torque.nodes-up'] = False

    def test_03_stop_scheduler(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(core.state['torque.pbs-sched-running'] == False, 'did not start pbs scheduler')

        command = ('service', 'pbs_sched', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop pbs scheduler')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(not os.path.exists(core.config['torque.sched-lockfile']),
                     'PBS server run lock file still present')

        files.restore(core.config['torque.pbs-nodes-file'], 'pbs')
        core.state['torque.pbs-sched-running'] = False

    def test_04_stop_munge(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(core.state['munge.running'] == False, 'munge not running')

        command = ('service', 'munge', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop munge daemon')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(not os.path.exists(core.config['munge.lockfile']),
                     'munge lock file still present')
        core.state['munge.running'] = False
        files.restore(core.config['munge.keyfile'], 'pbs')

    def test_05_restore_job_env(self):
        core.skip_ok_unless_installed(*self.required_rpms)

        files.restore(core.config['osg.job-environment'], owner='pbs')
        files.restore(core.config['osg.local-job-environment'], owner='pbs')
