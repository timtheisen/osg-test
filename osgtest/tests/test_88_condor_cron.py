import os
import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service
import unittest

class TestStopCondorCron(osgunittest.OSGTestCase):
    def test_01_stop_condor_cron(self):
        core.skip_ok_unless_installed('condor-cron')
        self.skip_ok_if(core.state['condor-cron.started-service'] == False, 'did not start server')

        if core.el_release() < 7:
            command = ('service', 'condor-cron', 'stop')
            stdout, _, fail = core.check_system(command, 'Stop Condor-Cron')
            self.assert_(stdout.find('error') == -1, fail)
        else:
            core.check_system(('systemctl', 'stop', 'condor-cron'), 'Stop Condor-Cron')

        self.assertFalse(service.is_running('condor-cron'), 'Condor-Cron still active')

        core.state['condor-cron.running-service'] = False
