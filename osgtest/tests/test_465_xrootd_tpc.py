import os
import pwd
import time

from ..library import core, files, osgunittest, xrootd


class TestXrootdTPC(osgunittest.OSGTestCase):
    rootdir_copied_file = f"{xrootd.ROOTDIR}/tpc_rootdir_copied_file.txt"

    # these will be set in test_00_setup:
    source_path = f"{xrootd.ROOTDIR}/{{public_subdir}}/test_tpc_source.txt"
    tpc1_source_url = f""
    dest_path = f"{xrootd.ROOTDIR}/{{public_subdir}}/test_gridftp_data_tpc.txt"
    public_copied_file = f"{xrootd.ROOTDIR}/{{public_subdir}}/tpc_public_copied_file.txt"
    public_copied_file2 = f"{xrootd.ROOTDIR}/{{public_subdir}}/tpc_public_copied_file2.txt"
    user_copied_file = f"{xrootd.ROOTDIR}/{{user_subdir}}/tpc_user_copied_file.txt"

    def tpc1_url_from_path(self, path):
        if path.startswith(xrootd.ROOTDIR):
            path = path[len(xrootd.ROOTDIR):]
        return f"https://{core.get_hostname()}:9001/{path}"

    def tpc2_url_from_path(self, path):
        if path.startswith(xrootd.ROOTDIR):
            path = path[len(xrootd.ROOTDIR):]
        return f"https://{core.get_hostname()}:9002/{path}"

    def copy_command(self, source_url, dest_url, source_token=None, dest_token=None):
        command = ["curl", "-A", "Test", "-vk", "-X", "COPY",
                   "-H", f"Source: {source_url}",
                   "-H", "Overwrite: T",
        ]
        if dest_token:
            command.extend(["-H", f"Authorization: Bearer {dest_token}"])
        if source_token:
            command.extend(["-H", f"Copy-Header:  Authorization: Bearer {source_token}"])
        command.append(dest_url)
        return command

    @core.elrelease(7,8)
    def setUp(self):
        core.skip_ok_unless_installed("osg-xrootd-standalone",
                                      by_dependency=True)
        if core.rpm_is_installed("xcache"):
            self.skip_ok_if(core.PackageVersion("xcache") >= "1.0.2", "xcache 1.0.2+ configs conflict with xrootd tests")
        self.skip_ok_unless(core.state['xrootd.is-configured'], "xrootd is not configured")

    def test_00_setup(self):
        public_subdir = core.config['xrootd.public_subdir']
        user_subdir = core.config['xrootd.user_subdir']
        for var in [
            "source_path",
            "public_copied_file",
            "public_copied_file2",
            "user_copied_file",
            "rootdir_copied_file",
        ]:
            setattr(TestXrootdTPC, var, getattr(TestXrootdTPC, var).format(**locals()))
        TestXrootdTPC.tpc1_source_url = self.tpc1_url_from_path(TestXrootdTPC.source_path)
        core.check_system(["cp", "/usr/share/osg-test/test_gridftp_data.txt", TestXrootdTPC.source_path],
                          "failed to prepare source file")

    def test_01_create_macaroons(self):
        self.skip_ok_unless("GSI" in core.config['xrootd.security'],
                            "Our macaroons tests use GSI")
        core.config['xrootd.tpc.macaroon-1'] = None
        core.config['xrootd.tpc.macaroon-2'] = None
        core.skip_ok_unless_installed('x509-scitokens-issuer-client', by_dependency=True)
        self.skip_bad_unless(core.state['proxy.valid'], 'requires a proxy cert')

        command = ('macaroon-init', self.tpc1_source_url, '20', 'READ_MATADATA,DOWNLOAD,LIST')

        status, stdout, stderr = core.system(command, user=True)
        fail = core.diagnose('Obtain Macaroon 1',
                             command, status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        core.config['xrootd.tpc.macaroon-1'] = stdout.strip()

        command = ('macaroon-init', self.tpc2_url_from_path(TestXrootdTPC.user_copied_file), '20', 'MANAGE,UPLOAD,LIST')
        status, stdout, stderr = core.system(command, user=True)
        fail = core.diagnose('Obtain Macaroon 2',
                             command, status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        core.config['xrootd.tpc.macaroon-2'] = stdout.strip()

    def test_02_initate_tpc_public(self):
        dest_path = TestXrootdTPC.public_copied_file
        try:
            os.unlink(dest_path)
        except FileNotFoundError:
            pass
        try:
            command = self.copy_command(TestXrootdTPC.tpc1_source_url,
                                        self.tpc2_url_from_path(dest_path))
            core.log_message("Unauth TPC to public dir")
            core.system(command, user=True)
            time.sleep(1)
            self.assertTrue(os.path.exists(dest_path), "Copied file missing")
            self.assertTrue(files.checksum_files_match(TestXrootdTPC.source_path, dest_path),
                            "Copied file contents do not match original")
        except AssertionError:
            core.state['xrootd.tpc.had-failures'] = True
            raise

    def test_03_initiate_tpc_denied(self):
        dest_path = TestXrootdTPC.user_copied_file
        try:
            os.unlink(dest_path)
        except FileNotFoundError:
            pass

        try:
            command = self.copy_command(TestXrootdTPC.tpc1_source_url,
                                        self.tpc2_url_from_path(dest_path))
            core.log_message("Unauth TPC to private dir (should fail)")
            core.system(command, user=True)
            time.sleep(1)
            self.assertFalse(os.path.exists(dest_path), "Copied file wrongly exists")
        except AssertionError:
            core.state['xrootd.tpc.had-failures'] = True
            raise

    def test_04_initiate_tpc_authenticated(self):
        token1 = token2 = ""
        # TODO Make these not be mutually exclusive
        if "GSI" in core.config['xrootd.security']:
            core.skip_ok_unless_installed('x509-scitokens-issuer-client', by_dependency=True)
            token1 = core.config['xrootd.tpc.macaroon-1']
            token2 = core.config['xrootd.tpc.macaroon-2']
            self.skip_bad_unless(token1 and token2, "TPC macaroons not created")
            security_type = "macaroons"
        elif "SCITOKENS" in core.config['xrootd.security']:
            core.skip_ok_unless_installed('xrootd-scitokens', by_dependency=True)
            token1 = core.state['token.xrootd_tpc_1_contents']
            token2 = core.state['token.xrootd_tpc_2_contents']
            self.skip_bad_unless(token1 and token2, "TPC SciTokens not created")
            security_type = "SciTokens"
        else:
            raise RuntimeError(f"Unexpected xrootd.security {core.config['xrootd.security']}")
            # ^^ should never get here - should be an ERROR instead of a FAIL

        dest_path = TestXrootdTPC.user_copied_file
        try:
            os.unlink(dest_path)
        except FileNotFoundError:
            pass

        try:
            command = self.copy_command(TestXrootdTPC.tpc1_source_url,
                                        self.tpc2_url_from_path(dest_path),
                                        source_token=token1,
                                        dest_token=token2)
            core.log_message(f"{security_type} auth TPC to private dir")
            core.system(command, user=True)
            time.sleep(1)
            self.assertTrue(os.path.exists(dest_path), "Copied file missing")
            self.assertTrue(files.checksum_files_match(TestXrootdTPC.source_path, dest_path), "Copied file contents do not match original")
        except AssertionError:
            core.state['xrootd.tpc.had-failures'] = True
            raise
