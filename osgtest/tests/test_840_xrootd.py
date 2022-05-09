import os
import shutil

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest
import osgtest.library.xrootd as xrootd


class TestStopXrootd(osgunittest.OSGTestCase):
    def setUp(self):
        if core.rpm_is_installed("xcache"):
            self.skip_ok_if(core.PackageVersion("xcache") >= "1.0.2",
                            "xcache 1.0.2+ configs conflict with xrootd tests")
        core.skip_ok_unless_installed("xrootd", "osg-xrootd-standalone", by_dependency=True)

    def test_01_dump_logs_if_failures(self):
        self.skip_ok_unless(core.state['xrootd.had-failures'], "no failures")
        self.skip_ok_unless(core.options.manualrun, "only dumping logs on a manual run (osg-test -m)")
        xrootd.dump_log(1000, "standalone")

    def test_02_stop_xrootd(self):
        if core.state['xrootd.backups-exist']:
            files.restore(core.config['xrootd.config'], "xrootd")
            files.restore(core.config['xrootd.logging-config'], "xrootd")
            files.restore(core.config['xrootd.authfile'], "xrootd")
            files.restore(xrootd.logfile("standalone"), "xrootd", ignore_missing=True)
            if "SCITOKENS" in core.config['xrootd.security']:
                files.restore('/etc/xrootd/scitokens.conf', "xrootd")
                files.remove("/etc/xrootd/config.d/99-osgtest-ztn.cfg", force=True)
            if os.path.exists(xrootd.ROOTDIR):
                shutil.rmtree(xrootd.ROOTDIR)

        # Get xrootd service back to its original state
        self.skip_ok_unless(core.state['xrootd.is-configured'], "xrootd is not configured")
        xrootd_service = core.config['xrootd_service']
        if service.is_running(xrootd_service):
            service.check_stop(xrootd_service, force=True)
        if core.state.get('xrootd.service-was-running', False):
            service.check_start(xrootd_service, force=True)

