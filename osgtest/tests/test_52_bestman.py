import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import socket
import tempfile
import unittest

class TestBestman(osgunittest.OSGTestCase):

    __data_path = '/usr/share/osg-test/test_gridftp_data.txt'
    __port = '10443'
    __sfn = 'srm/v2/server'
    __hostname = socket.getfqdn()


    def setUp(self):
        core.skip_ok_unless_installed('bestman2-server', 'bestman2-client', 'voms-clients')
        self.skip_bad_unless(core.state['bestman.server-running'], 'bestman server not running')

    def get_srm_url_base(self):
        return 'srm://%s:%s/%s?SFN=' % (TestBestman.__hostname, TestBestman.__port, TestBestman.__sfn)

    def get_srm_url(self):
        return self.get_srm_url_base() + TestBestman.__remote_path

    def setup_temp_paths(self):
        TestBestman.__temp_dir = tempfile.mkdtemp()
        TestBestman.__remote_path = TestBestman.__temp_dir + '/bestman_put_copied_file.txt'
        TestBestman.__local_path = TestBestman.__temp_dir + '/bestman_get_copied_file.txt'

    def test_01_ping(self):
        command = ('srm-ping', self.get_srm_url_base(), '-debug')
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman Ping', status, stdout, stderr)
        self.assertEqual(status, 0, fail) 
 
    def test_02_copy_local_to_server(self):
        self.setup_temp_paths()
        os.chmod(TestBestman.__temp_dir, 0777)
        command = ('srm-copy', 'file://' + TestBestman.__data_path, self.get_srm_url(), '-debug')
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman copy, local to URL', status, stdout, stderr)
        file_copied = os.path.exists(TestBestman.__remote_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_03_copy_server_to_local(self):
        command = ('srm-copy', self.get_srm_url(), 'file://' + TestBestman.__local_path, '-debug')
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman copy, URL to local', status, stdout, stderr)
        file_copied = os.path.exists(TestBestman.__local_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')
        files.remove(TestBestman.__local_path)

    def test_04_remove_server_file(self):
        command = ('srm-rm', self.get_srm_url(), '-debug')
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman remove, URL file', status, stdout, stderr)
        file_removed = not os.path.exists(TestBestman.__remote_path)    
        self.assertEqual(status, 0, fail)
        self.assert_(file_removed, 'Copied file still exists') 
        files.remove(TestBestman.__temp_dir) 

