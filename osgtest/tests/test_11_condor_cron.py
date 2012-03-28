import os
import osgtest.library.core as core
import unittest

class TestStartCondorCron(unittest.TestCase):

    def test_01_start_condor_cron(self):
        core.config['condor-cron.lockfile'] = '/var/lock/subsys/condor-cron'
        core.state['condor-cron.started-service'] = False
        core.state['condor-cron.running-service'] = False

        if core.missing_rpm('condor-cron'):
            return
        if os.path.exists(core.config['condor-cron.lockfile']):
            core.state['condor-cron.running-service'] = True
            core.skip('already running')
            return

        command = ('service', 'condor-cron', 'start')
        stdout, _, fail = core.check_system(command, 'Start Condor-Cron')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['condor-cron.lockfile']),
                     'Condor-Cron run lock file missing')
        core.state['condor-cron.started-service'] = True
