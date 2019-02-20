import os
import json
import pwd
import requests

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest


class TestXrootdTPC(osgunittest.OSGTestCase):

    def test_01_create_macaroons(self):
        core.skip_ok_unless_installed('xrootd', 'xrootd-scitokens', 'x509-scitokens-issuer-client', by_dependency=True)
        self.skip_bad_unless(core.state['proxy.created'], 'Proxy creation failed')
        
        uid = pwd.getpwnam(core.options.username)[2]
        usercert = '/tmp/x509up_u%d' % uid
        userkey = '/tmp/x509up_u%d' % uid
        
        core.config['xrootd.tpc.url-1'] = "https://" + core.get_hostname() + ":9001" + "/usr/share/osg-test/test_gridftp_data.txt"
        command = ('macaroon-init', core.config['xrootd.tpc.url-1'], '20', 'DOWNLOAD')

        status, stdout, stderr = core.system(command, user=True)
        fail = core.diagnose('Obtain Macaroon one',
                             command, status, stdout, stderr)
        core.config['xrootd.tpc.macaroon-1'] = stdout.strip('\n')

        core.config['xrootd.tpc.url-2'] = "https://" + core.get_hostname() + ":9002" + "/tmp/test_gridftp_data_tpc.txt"
        command = ('macaroon-init', core.config['xrootd.tpc.url-2'], '20', 'UPLOAD')
        status, stdout, stderr = core.system(command, user=True)
        fail = core.diagnose('Obtain Macaroon number two',
                             command, status, stdout, stderr)
        core.config['xrootd.tpc.macaroon-2'] = stdout.strip('\n')
        

    def test_02_initate_tpc(self):
        core.skip_ok_unless_installed('xrootd', 'xrootd-scitokens', by_dependency=True)
        session = requests.Session()
        session.verify = False
        headers = {}
        headers['Overwrite'] = 'T'
        headers['Authorization'] = 'Bearer %s' % core.config['xrootd.tpc.macaroon-1']
        headers['Source'] = core.config['xrootd.tpc.url-1']
        headers['Copy-Header'] = 'Authorization: Bearer %s' % core.config['xrootd.tpc.macaroon-2']
        resp = session.request('COPY',
                               core.config['xrootd.tpc.url-2'], headers=headers,
                               allow_redirects=True)
        file_copied = os.path.exists("/tmp/test_gridftp_data_tpc.txt")
        self.assert_(file_copied, 'Copied file missing')
        chechskum_match = files.checksum_files_match("/tmp/test_gridftp_data_tpc.txt", "/usr/share/osg-test/test_gridftp_data.txt")
        self.assert_(chechskum_match, 'Files have same contents')

        
