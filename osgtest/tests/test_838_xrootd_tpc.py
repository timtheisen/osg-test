import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStopXrootdTPC(osgunittest.OSGTestCase):
    @core.elrelease(7,8)
    def setUp(self):
        core.skip_ok_unless_installed("xrootd",
                                      by_dependency=True)

    def test_01_stop_xrootd(self):
        if core.state['xrootd.tpc.backups-exist']:
            files.restore(core.config['xrootd.tpc.config-1'], "xrootd")
            files.restore(core.config['xrootd.tpc.config-2'], "xrootd")

        self.skip_ok_if(not core.state['xrootd.started-http-server-1'] and
                        not core.state['xrootd.started-http-server-2'], 
                        'did not start any of the http servers')
        service.check_stop(core.config['xrootd_tpc_service_1'])
        service.check_stop(core.config['xrootd_tpc_service_2'])

    def test_02_clean_test_files(self):
        files.remove("/tmp/test_gridftp_data_tpc.txt", force=True)
