import os
import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStartCondorCron(osgunittest.OSGTestCase):
    def test_01_start_condor_cron(self):
        core.state['condor-cron.started-service'] = False
        core.state['condor-cron.running-service'] = False

        core.skip_ok_unless_installed('condor-cron')
        if service.is_running('condor-cron', timeout=1):
            core.state['condor-cron.running-service'] = True
            self.skip_ok('already running')

        service.check_start('condor-cron')

        core.state['condor-cron.started-service'] = True
        core.state['condor-cron.running-service'] = True
