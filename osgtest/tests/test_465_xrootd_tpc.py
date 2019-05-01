import os
import json
import pwd

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest


class TestXrootdTPC(osgunittest.OSGTestCase):
    @core.elrelease(7,8)
    def setUp(self):
        core.skip_ok_unless_installed("xrootd",
                                      by_dependency=True)

    def test_01_create_macaroons(self):
        core.skip_ok_unless_installed('x509-scitokens-issuer-client', by_dependency=True)
        self.skip_bad_unless(core.state['proxy.created'], 'Proxy creation failed')
        core.config['xrootd.tpc.macaroon-1'] = None
        core.config['xrootd.tpc.macaroon-2'] = None
        
        uid = pwd.getpwnam(core.options.username)[2]
        usercert = '/tmp/x509up_u%d' % uid
        userkey = '/tmp/x509up_u%d' % uid
        
        core.config['xrootd.tpc.url-1'] = "https://" + core.get_hostname() + ":9001" + "/usr/share/osg-test/test_gridftp_data.txt".strip()
        command = ('macaroon-init', core.config['xrootd.tpc.url-1'], '20', 'DOWNLOAD')

        status, stdout, stderr = core.system(command, user=True)
        fail = core.diagnose('Obtain Macaroon one',
                             command, status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        core.config['xrootd.tpc.macaroon-1'] = stdout.strip()

        core.config['xrootd.tpc.url-2'] = "https://" + core.get_hostname() + ":9002" + "/tmp/test_gridftp_data_tpc.txt".strip()
        command = ('macaroon-init', core.config['xrootd.tpc.url-2'], '20', 'UPLOAD')
        status, stdout, stderr = core.system(command, user=True)
        fail = core.diagnose('Obtain Macaroon number two',
                             command, status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        core.config['xrootd.tpc.macaroon-2'] = stdout.strip()
        
    def test_02_initate_tpc(self):
        core.skip_ok_unless_installed('x509-scitokens-issuer-client', by_dependency=True)
        self.skip_bad_if(core.config['xrootd.tpc.macaroon-1'] is None, 'Macaroon creation failed earlier')
        self.skip_bad_if(core.config['xrootd.tpc.macaroon-2'] is None, 'Macaroon creation failed earlier')
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
