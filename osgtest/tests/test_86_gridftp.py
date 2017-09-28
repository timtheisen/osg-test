import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStopGridFTP(osgunittest.OSGTestCase):

    def test_01_stop_gridftp(self):
        core.skip_ok_unless_installed('globus-gridftp-server-progs')
        self.skip_ok_if(core.state['gridftp.started-server'] == False, 'did not start server')
        service.check_stop('globus-gridftp-server')
        core.state['gridftp.running-server'] = False

    def test_02_restore_auth(self):
        if core.osg_release() < 3.4:
            return

        core.skip_ok_unless_installed('globus-gridftp-server-progs', 'lcmaps-plugins-voms')
        files.restore(core.config['gridftp.env'], 'gridftp')
