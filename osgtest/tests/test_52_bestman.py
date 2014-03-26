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
    __temp_dir = tempfile.mkdtemp()
    __hostname = socket.getfqdn()
    __remote_path = __temp_dir + '/bestman_put_copied_file.txt'
    __local_path = __temp_dir + '/bestman_get_copied_file.txt'


    def setUp(self):
        core.skip_ok_unless_installed('bestman2-server', 'voms-clients')
        self.skip_bad_unless(core.state['bestman.server-running'], 'bestman server not running')

    def get_srm_url_base(self):
        return 'srm://%s:%s/%s?SFN=' % (TestBestman.__hostname, TestBestman.__port, TestBestman.__sfn)

    def get_srm_url(self):
        return self.get_srm_url_base() + TestBestman.__remote_path

    def test_01_ping(self):
        core.skip_ok_unless_installed('bestman2-client')
        command = ('srm-ping', self.get_srm_url_base())
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman Ping', status, stdout, stderr)
        self.assertEqual(status, 0, fail) 
 
    def test_02_copy_local_to_server(self):
        core.skip_ok_unless_installed('bestman2-client')
        os.chmod(TestBestman.__temp_dir, 0777)
        command = ('srm-copy', 'file:///' + TestBestman.__data_path, self.get_srm_url(), '-debug')
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman copy, local to URL', status, stdout, stderr)
        file_copied = os.path.exists(TestBestman.__remote_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_03_copy_server_to_local(self):
        core.skip_ok_unless_installed('bestman2-client')
        command = ('srm-copy', self.get_srm_url(), 'file:///' + TestBestman.__local_path)
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman copy, URL to local', status, stdout, stderr)
        file_copied = os.path.exists(TestBestman.__local_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')
        files.remove(TestBestman.__local_path)

    def test_04_remove_server_file(self):
        core.skip_ok_unless_installed('bestman2-client')
        command = ('srm-rm', self.get_srm_url())
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman remove, URL file', status, stdout, stderr)
        file_removed = not os.path.exists(TestBestman.__remote_path)    
        self.assertEqual(status, 0, fail)
        self.assert_(file_removed, 'Copied file still exists') 
        files.remove(TestBestman.__temp_dir) 

    def test_05_copy_local_to_server_lcg_util(self):
        core.skip_ok_unless_installed('lcg-util')
        os.chmod(TestBestman.__temp_dir, 0777)
        command = ('lcg-cp', '-v', '-b', '-D', 'srmv2', 'file:///' + TestBestman.__data_path, self.get_srm_url())
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('lcg-util copy, local to URL',
                             status, stdout, stderr)
        file_copied = os.path.exists(TestBestman.__remote_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_06_copy_server_to_local_lcg_util(self):
        core.skip_ok_unless_installed('lcg-util')
        command = ('lcg-cp', '-v', '-b', '-D', 'srmv2', self.get_srm_url(), 'file:///' + TestBestman.__local_path)
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('lcg-util copy, URL to local',
                             status, stdout, stderr)
        file_copied = os.path.exists(TestBestman.__local_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')
        files.remove(TestBestman.__local_path)

    def test_07_remove_server_file_lcg_util(self):
        core.skip_ok_unless_installed('lcg-util')
        command = ('lcg-del', '-v', '-b', '-l', '-D', 'srmv2', self.get_srm_url())
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('lcg-util remove, URL file',
                             status, stdout, stderr)
        file_removed = not os.path.exists(TestBestman.__remote_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_removed, 'Copied file still exists')
        files.remove(TestBestman.__temp_dir)
