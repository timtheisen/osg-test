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
        core.config['xrootd.tpc.macaroon-1'] = None
        core.config['xrootd.tpc.macaroon-2'] = None
        core.skip_ok_unless_installed('x509-scitokens-issuer-client', by_dependency=True)
        self.skip_bad_unless(core.state['proxy.valid'], 'requires a proxy cert')
        uid = pwd.getpwnam(core.options.username)[2]
        usercert = '/tmp/x509up_u%d' % uid
        userkey = '/tmp/x509up_u%d' % uid
        
        core.config['xrootd.tpc.url-1'] = "https://" + core.get_hostname() + ":9001" + "/usr/share/osg-test/test_gridftp_data.txt".strip()
        command = ('macaroon-init', core.config['xrootd.tpc.url-1'], '20', 'ALL')

        status, stdout, stderr = core.system(command, user=True)
        fail = core.diagnose('Obtain Macaroon 1',
                             command, status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        core.config['xrootd.tpc.macaroon-1'] = stdout.strip()

        core.config['xrootd.tpc.url-2'] = "https://" + core.get_hostname() + ":9002" + "/tmp/test_gridftp_data_tpc.txt".strip()
        command = ('macaroon-init', core.config['xrootd.tpc.url-2'], '20', 'ALL')
        status, stdout, stderr = core.system(command, user=True)
        fail = core.diagnose('Obtain Macaroon 2',
                             command, status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        core.config['xrootd.tpc.macaroon-2'] = stdout.strip()
        
    def test_02_initate_tpc(self):
        core.skip_ok_unless_installed('x509-scitokens-issuer-client', by_dependency=True)
        self.skip_bad_if(core.config['xrootd.tpc.macaroon-1'] is None, 'Macaroon 1 creation failed earlier')
        self.skip_bad_if(core.config['xrootd.tpc.macaroon-2'] is None, 'Macaroon 2 creation failed earlier')
        headers = {}
        command = ('curl', '-A', 'Test', "-vk", "-X", "COPY",
                   '-H', "Authorization: Bearer %s" % core.config['xrootd.tpc.macaroon-1'],
                   '-H', "Source: %s" % core.config['xrootd.tpc.url-1'], 
                   '-H', 'Overwrite: T', 
                   '-H', 'Copy-Header:  Authorization: Bearer %s'% core.config['xrootd.tpc.macaroon-2'],
                   core.config['xrootd.tpc.url-2'])
        status, stdout, stderr = core.system(command, user=True)
        fail = core.diagnose('Initiate third party copy',
                             command, status, stdout, stderr)
        file_copied = os.path.exists("/tmp/test_gridftp_data_tpc.txt")
        self.assert_(file_copied, 'Copied file missing')
        chechskum_match = files.checksum_files_match("/tmp/test_gridftp_data_tpc.txt", "/usr/share/osg-test/test_gridftp_data.txt")
        self.assert_(chechskum_match, 'Files have same contents')
