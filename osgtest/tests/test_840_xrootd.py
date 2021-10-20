import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest


class TestStopXrootd(osgunittest.OSGTestCase):
    def setUp(self):
        if core.rpm_is_installed("xcache"):
            self.skip_ok_if(core.PackageVersion("xcache") >= "1.0.2",
                            "xcache 1.0.2+ configs conflict with xrootd tests")
        core.skip_ok_unless_installed("xrootd", "osg-xrootd-standalone", by_dependency=True)


    def test_01_stop_xrootd(self):
        if core.state['xrootd.backups-exist']:
            files.restore(core.config['xrootd.config'], "xrootd")
            files.restore(core.config['xrootd.logging-config'], "xrootd")
            files.restore('/etc/xrootd/auth_file', "xrootd")
            if not core.rpm_is_installed('xrootd-lcmaps'):
                files.restore('/etc/grid-security/xrd/xrdmapfile', "xrootd")
        core.skip_ok_unless_installed('xrootd', 'globus-proxy-utils', by_dependency=True)
        self.skip_ok_if(core.state['xrootd.started-server'], 'did not start server')
        service.check_stop(core.config['xrootd_service'])
        files.remove(core.config['xrootd.tmp-dir'], force=True)
