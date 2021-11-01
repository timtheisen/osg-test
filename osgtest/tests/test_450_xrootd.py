import os
import socket
import shutil
import tempfile
import pwd

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service
import osgtest.library.xrootd as xrootd


ERR_AUTH_FAIL = 52
ERR_PERMISSION_DENIED = 54

HOSTNAME = core.get_hostname() or "localhost"


def xrootd_record_failure(fn):
    """Decorator for xrootd tests that sets the core.state['xrootd.had-failures'] flag
    if there were any test failures.

    """
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (osgunittest.OkSkipException, osgunittest.BadSkipException, osgunittest.ExcludedException):
            raise
        except AssertionError:
            core.state['xrootd.had-failures'] = True
            raise
    return inner


class TestXrootd(osgunittest.OSGTestCase):

    __data_path = '/usr/share/osg-test/test_gridftp_data.txt'
    __fuse_path = '/mnt/xrootd_fuse_test'

    public_copied_file = f"{xrootd.ROOTDIR}/{{public_subdir}}/public_copied_file.txt"
    public_copied_file2 = f"{xrootd.ROOTDIR}/{{public_subdir}}/public_copied_file2.txt"
    user_copied_file = f"{xrootd.ROOTDIR}/{{user_subdir}}/user_copied_file.txt"
    file_to_download = f"{xrootd.ROOTDIR}/{{public_subdir}}/file_to_download.txt"
    rootdir_copied_file = f"{xrootd.ROOTDIR}/rootdir_copied_file.txt"

    def setUp(self):
        if core.rpm_is_installed("xcache"):
            self.skip_ok_if(core.PackageVersion("xcache") >= "1.0.2",
                            "xcache 1.0.2+ configs conflict with xrootd tests")
        core.skip_ok_unless_installed("xrootd", "xrootd-client", "osg-xrootd-standalone", by_dependency=True)
        self.skip_ok_unless(core.state['xrootd.is-configured'], "xrootd is not configured")

    def xrootd_url(self, path, add_token=True):
        if path.startswith(xrootd.ROOTDIR):
            path = path[len(xrootd.ROOTDIR):]
        url = f"root://{socket.getfqdn()}/{path}"
        if (
                add_token and
                "SCITOKENS" in core.config['xrootd.security'] and
                not core.config['xrootd.ztn']
        ):
            url += f"?authz=Bearer%20{core.state['token.xrootd_contents']}"
        return url

    def skip_unless_security(self, security):
        if security not in core.config['xrootd.security']:
            self.skip_ok("Not testing xrootd with %s" % security)
        if security == "GSI":
            self.skip_bad_unless(core.state['proxy.valid'], "no valid proxy")
        elif security == "SCITOKENS":
            self.skip_bad_unless(core.state['token.xrootd_contents'], "xrootd scitoken is missing or empty")
            self.skip_bad_unless(os.path.isfile(core.config['token.xrootd']), "xrootd scitoken file is missing")
        elif security == "VOMS":
            self.skip_bad_unless(core.state['voms.got-proxy'], "no valid proxy with voms attributes")

    def test_00_setup(self):
        public_subdir = core.config['xrootd.public_subdir']
        user_subdir = core.config['xrootd.user_subdir']
        for var in [
            "public_copied_file",
            "public_copied_file2",
            "user_copied_file",
            "file_to_download",
            "rootdir_copied_file",
        ]:
            setattr(TestXrootd, var, getattr(TestXrootd, var).format(**locals()))


    def test_03a_xrdcp_upload_gsi_authenticated(self):
        self.skip_ok_unless("GSI" in core.config['xrootd.security'], "not using GSI")
        self.skip_bad_unless(core.state['proxy.valid'], "no valid proxy")
        try:
            self.skip_bad_unless_running(core.config['xrootd_service'])
            xrootd_url = self.xrootd_url(TestXrootd.user_copied_file)
            command = ('xrdcp', '--debug', '3', TestXrootd.__data_path, xrootd_url)
            core.check_system(command, "Authenticated xrdcp upload to private dir", user=True)
            self.assert_(os.path.exists(TestXrootd.user_copied_file), "Uploaded file missing")
        except AssertionError:
            core.state['xrootd.had-failures'] = True
            raise

    def test_03b_xrdcp_upload_scitoken_authenticated(self):
        self.skip_ok_unless("SCITOKENS" in core.config['xrootd.security'], "not using scitokens")
        token_contents = core.state['token.xrootd_contents']
        self.skip_bad_unless(token_contents, "xrootd scitoken not found")
        try:
            self.skip_bad_unless_running(core.config['xrootd_service'])
            bearer_token = token_contents if core.config['xrootd.ztn'] else None
            with core.no_x509(core.options.username), core.environ_context({"BEARER_TOKEN": bearer_token}):
                xrootd_url = self.xrootd_url(TestXrootd.user_copied_file)
                command = ('xrdcp', '--debug', '3', TestXrootd.__data_path, xrootd_url)
                core.check_system(command, "Authenticated xrdcp upload to private dir", user=True)
                self.assert_(os.path.exists(TestXrootd.user_copied_file), "Uploaded file missing")
        except AssertionError:
            core.state['xrootd.had-failures'] = True
            raise

    def test_04a_xrdcp_upload_gsi_authenticated_denied(self):
        self.skip_ok_unless("GSI" in core.config['xrootd.security'], "not using GSI")
        try:
            self.skip_bad_unless_running(core.config['xrootd_service'])
            xrootd_url = self.xrootd_url(TestXrootd.rootdir_copied_file, add_token=False)
            command = ('xrdcp', '--debug', '3', TestXrootd.__data_path, xrootd_url)
            core.check_system(command, "Authenticated xrdcp upload to dir w/o write access (should be denied)", exit=ERR_PERMISSION_DENIED, user=True)
            self.assertFalse(os.path.exists(TestXrootd.rootdir_copied_file), "Uploaded file wrongly present")
        except AssertionError:
            core.state['xrootd.had-failures'] = True
            raise
        finally:
            try:
                files.remove(TestXrootd.rootdir_copied_file)
            except FileNotFoundError:
                pass

    def test_04b_xrdcp_upload_scitoken_authenticated_denied(self):
        self.skip_ok_unless("SCITOKENS" in core.config['xrootd.security'], "not using scitokens")
        token_contents = core.state['token.xrootd_contents']
        self.skip_bad_unless(token_contents, "xrootd scitoken not found")
        try:
            self.skip_bad_unless_running(core.config['xrootd_service'])
            bearer_token = token_contents if core.config['xrootd.ztn'] else None
            with core.no_x509(core.options.username), core.environ_context({"BEARER_TOKEN": bearer_token}):
                xrootd_url = self.xrootd_url(TestXrootd.rootdir_copied_file)
                command = ('xrdcp', '--debug', '3', TestXrootd.__data_path, xrootd_url)
                core.check_system(command, "Authenticated xrdcp upload to dir w/o write access (should be denied)", exit=ERR_PERMISSION_DENIED, user=True)
                self.assertFalse(os.path.exists(TestXrootd.rootdir_copied_file), "Uploaded file wrongly present")
        except AssertionError:
            core.state['xrootd.had-failures'] = True
            raise

    def test_05_xrootd_multiuser(self):
        core.skip_ok_unless_installed('xrootd-multiuser', by_dependency=True)
        self.skip_bad_unless(core.config['xrootd.multiuser'], 'Xrootd not configured for multiuser')
        try:
            file_path = TestXrootd.user_copied_file
            self.skip_bad_unless(os.path.exists(file_path), "uploaded file does not exist")
            self.skip_bad_unless(os.path.isfile(file_path), "uploaded file exists but is not a regular file")

            # Ownership check; copied from core.check_file_ownership() because I want more detailed info
            try:
                file_stat = os.stat(file_path)
            except OSError as err:
                self.fail(f"Unexpected error while statting uploaded file: {err}")
            file_owner_uid = file_stat.st_uid
            username = core.options.username
            file_owner_name = pwd.getpwuid(file_owner_uid).pw_name
            self.assertEqual(file_owner_name, username,
                             f"file owner {file_owner_name} does not match expected user {username}")
        except AssertionError:
            core.state['xrootd.had-failures'] = True
            raise

    def test_06_xrdcp_download_public(self):
        if "GSI" in core.config['xrootd.security']:
            # We need a proxy if we're configured for GSI, even if we're reading from a public location
            self.skip_bad_unless(core.state['proxy.valid'], "no valid proxy")
        file_text = "This is some test data for an xrootd test."
        download_path = f"/tmp/osgtest-download.{os.getpid()}.txt"
        try:
            self.skip_bad_unless_running(core.config['xrootd_service'])
            with open(TestXrootd.file_to_download, "w") as f:
                f.write(file_text)
            os.chown(TestXrootd.file_to_download, core.state['user.uid'], core.state['user.gid'])
            os.chmod(TestXrootd.file_to_download, 0o644)
            xrootd_url = self.xrootd_url(TestXrootd.file_to_download)
            command = ('xrdcp', '--debug', '3', xrootd_url, download_path)
            core.check_system(command, "xrdcp download from public dir", user=True)
            self.assertTrue(os.path.exists(download_path), "Downloaded file missing")
            self.assertEqual(files.read(download_path, as_single_string=True), file_text,
                             "Downloaded contents differ from expected")
        except AssertionError:
            core.state['xrootd.had-failures'] = True
            raise
        finally:
            try:
                os.unlink(download_path)
            except FileNotFoundError:
                pass

    # TODO Drop after we EOL OSG 3.5
    # Test dir reorg broke the FUSE test.  We can drop it for now due to low demand -mat 2021-10-14
    # def test_07_xrootd_fuse(self):
    #     # This tests xrootd-fuse using a mount in /mnt
    #     core.skip_ok_unless_installed('xrootd-fuse')
    #     self.skip_ok_unless(os.path.exists("/mnt"), "/mnt did not exist")
    #
    #     if not os.path.exists(TestXrootd.__fuse_path):
    #         os.mkdir(TestXrootd.__fuse_path)
    #
    #     public_dir = xrootd.ROOTDIR + core.config['xrootd.public_subdir']
    #
    #     try:
    #         self.skip_bad_unless_running(core.config['xrootd_service'])
    #         # TODO: How to pass a scitoken to the mount?
    #         # For some reason, sub process hangs on fuse processes, use os.system
    #         cmd = f"mount -t fuse -o rdr=root://localhost/{public_dir},uid=xrootd xrootdfs {TestXrootd.__fuse_path}"
    #         core.log_message(cmd)
    #         ret = os.system(cmd)
    #         self.assertEqual(ret, 0, f"FUSE mount failed with code {ret}")
    #         try:
    #             core.system(["ls", "-l", os.path.dirname(TestXrootd.__fuse_path)])
    #             self.assertTrue(os.path.exists(TestXrootd.__fuse_path), "FUSE mounted filesystem is broken")
    #             # Copy a file in and see if it made it into the fuse mount
    #             xrootd_url = self.xrootd_url(TestXrootd.public_copied_file2)
    #             core.system(['xrdcp', '--debug', '3', TestXrootd.__data_path, xrootd_url], user=True)
    #             core.system(['find', TestXrootd.__fuse_path, '-ls'])
    #             rel_copied_file2 = os.path.relpath(TestXrootd.public_copied_file2, public_dir)
    #             fuse_copied_file2 = os.path.join(TestXrootd.__fuse_path, rel_copied_file2)
    #             self.assert_(os.path.isfile(fuse_copied_file2), f"Test file not uploaded to FUSE mount at {fuse_copied_file2}")
    #             files.remove(TestXrootd.public_copied_file2)
    #         finally:
    #             core.system(['umount', TestXrootd.__fuse_path])
    #     except AssertionError:
    #         core.state['xrootd.had-failures'] = True
    #         raise
    #     finally:
    #         os.rmdir(TestXrootd.__fuse_path)
