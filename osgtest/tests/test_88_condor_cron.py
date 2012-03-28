import os
import osgtest.library.core as core
import unittest

class TestStopCondorCron(unittest.TestCase):

    def test_01_stop_condor_cron(self):
        if core.missing_rpm('condor-cron'):
            return
        if core.state['condor-cron.started-service'] == False:
            core.skip('did not start server')
            return

        command = ('service', 'condor-cron', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop Condor-Cron')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(not os.path.exists(core.config['condor-cron.lockfile']),
                     'Condor-Cron run lock file still present')

        core.state['condor-cron.running-service'] = False
