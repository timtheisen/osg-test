import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest


class TestStopRSV(osgunittest.OSGTestCase):

    def setUp(self):
        if core.osg_release() != '3.4':
            raise osgunittest.ExcludedException("excluding for OSG %s" % core.osg_release().version)

    def test_01_stop_rsv(self):
        core.skip_ok_unless_installed('rsv')
        self.skip_ok_if(core.state['rsv.started-service'] == False, 'did not start service')
        service.check_stop('rsv')
        core.state['rsv.running-service'] = False

    def test_02_restore_config(self):
        core.skip_ok_unless_installed('rsv')
        files.restore(core.config['system.mapfile'], 'rsv')
