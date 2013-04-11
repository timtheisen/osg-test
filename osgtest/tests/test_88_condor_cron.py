import os
import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import unittest

class TestStopCondorCron(osgunittest.OSGTestCase):

    def test_01_stop_condor_cron(self):
        core.skip_ok_unless_installed('condor-cron')
        self.skip_ok_if(core.state['condor-cron.started-service'] == False, 'did not start server')



        command = ('service', 'condor-cron', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop Condor-Cron')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(not os.path.exists(core.config['condor-cron.lockfile']),
                     'Condor-Cron run lock file still present')

        core.state['condor-cron.running-service'] = False
