import os

from osgtest.library import core, service, osgunittest

@core.osgrelease(3.4)
class TestStartRSV(osgunittest.OSGTestCase):

    def test_01_config(self):
        pass

    def test_02_start_rsv(self):
        core.config['rsv.lockfile'] = "/var/lock/subsys/rsv"
        core.state['rsv.started-service'] = False
        core.state['rsv.running-service'] = False

        core.skip_ok_unless_installed('rsv')

        # Is RSV already running?
        if os.path.exists(core.config['rsv.lockfile']):
            core.state['rsv.running-service'] = True
            self.skip_ok('already running')

        # Before we start RSV, make sure Condor-Cron is up
        self.skip_bad_unless(core.state['condor-cron.running-service'], 'Condor-Cron not running')

        service.check_start('rsv')
        core.state['rsv.started-service'] = True
        core.state['rsv.running-service'] = True
