import os
import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service
import unittest

class TestStartCondorCron(osgunittest.OSGTestCase):
    def test_01_start_condor_cron(self):
        core.state['condor-cron.started-service'] = False
        core.state['condor-cron.running-service'] = False

        core.skip_ok_unless_installed('condor-cron')
        if service.is_running('condor-cron'):
            core.state['condor-cron.running-service'] = True
            self.skip_ok('already running')

        if core.el_release() < 7:
            command = ('service', 'condor-cron', 'start')
            stdout, _, fail = core.check_system(command, 'Start Condor-Cron')
            self.assert_(stdout.find('error') == -1, fail)
        else:
            core.check_system(('systemctl', 'start', 'condor-cron'), 'Start Condor-Cron')

        self.assert_(service.is_running('condor-cron'), "Condor-Cron is not running")

        core.state['condor-cron.started-service'] = True
        core.state['condor-cron.running-service'] = True
