import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStopXrootd(osgunittest.OSGTestCase):

    def test_01_stop_xrootd(self):
        if (core.config['xrootd.gsi'] == "ON") and (core.state['xrootd.backups-exist'] == True):
            files.restore('/etc/xrootd/xrootd-clustered.cfg', "xrootd")
            files.restore('/etc/xrootd/auth_file', "xrootd")
            files.restore('/etc/grid-security/xrd/xrdmapfile', "xrootd")
        core.skip_ok_unless_installed('xrootd', by_dependency=True)
        self.skip_ok_if(core.state['xrootd.started-server'] == False, 'did not start server')
        service.stop(core.config['xrootd_service'])

