import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStopRSV(osgunittest.OSGTestCase):

    def test_01_stop_rsv(self):
        core.skip_ok_unless_installed('rsv')
        self.skip_ok_if(core.state['rsv.started-service'] == False, 'did not start service')

        service.stop('rsv')
        self.assert_(not service.is_running('rsv'), 'RSV failed to stop')

        core.state['rsv.running-service'] = False

    def test_02_restore_config(self):
        core.skip_ok_unless_installed('rsv')
        files.restore(core.config['system.mapfile'], 'rsv')
