import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStopXrootd(osgunittest.OSGTestCase):

    def test_01_stop_xrootd(self):
        if core.state['xrootd.backups-exist']:
            if core.PackageVersion('xrootd') < '1:4.9.0':
                files.restore(core.config['xrootd.config'], "xrootd")
            else:
                files.restore(core.config['xrootd.config-extra'], "xrootd")
            files.restore('/etc/xrootd/auth_file', "xrootd")
            if not core.rpm_is_installed('xrootd-lcmaps'):
                files.restore('/etc/grid-security/xrd/xrdmapfile', "xrootd")
        core.skip_ok_unless_installed('xrootd', by_dependency=True)
        self.skip_ok_if(core.state['xrootd.started-server'], 'did not start server')
        service.check_stop(core.config['xrootd_service'])
        files.remove(core.config['xrootd.tmp-dir'], force=True)
