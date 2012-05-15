import os
import osgtest.library.core as core
import osgtest.library.files as files
import socket
import tempfile
import unittest

class TestBestman(unittest.TestCase):

    __data_path = '/usr/share/osg-test/test_gridftp_data.txt'
    __port = '10443'
    __sfn = 'srm/v2/server'
    __temp_dir = tempfile.mkdtemp()
    __hostname = socket.getfqdn()
    __remote_path = __temp_dir + '/bestman_put_copied_file.txt'
    __local_path = __temp_dir + '/bestman_get_copied_file.txt'

    def test_01_ping(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client', 'voms-clients'):
           return
        srm_url = 'srm://%s:' % (TestBestman.__hostname)
        command = ('srm-ping', srm_url + TestBestman.__port + '/' + TestBestman.__sfn )
        status, stdout, stderr = core.system(command, True)
	fail = core.diagnose('Bestman Ping',
                             status, stdout, stderr)
        self.assertEqual(status, 0, fail) 
 
    def test_02_copy_local_to_server(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client', 'voms-clients'):
           return
        os.chmod(TestBestman.__temp_dir, 0777)
        srm_url = 'srm://%s:%s/%s?SFN=%s' % (TestBestman.__hostname, TestBestman.__port, TestBestman.__sfn, TestBestman.__remote_path)
        command = ('srm-copy', 'file:///' + TestBestman.__data_path,srm_url)
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman copy, local to URL',
                             status, stdout, stderr)
        file_copied = os.path.exists(TestBestman.__remote_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_03_copy_server_to_local(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client', 'voms-clients'):     
	   return
	srm_url = 'srm://%s:%s/%s?SFN=%s' % (TestBestman.__hostname, TestBestman.__port, TestBestman.__sfn, TestBestman.__remote_path)
	command = ('srm-copy', srm_url, 'file:///' + TestBestman.__local_path)
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman copy, URL to local',
                             status, stdout, stderr)
        file_copied = os.path.exists(TestBestman.__local_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')
	files.remove(TestBestman.__local_path)

    def test_04_remove_server_file(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client', 'voms-clients'):
           return
        srm_url = 'srm://%s:%s/%s?SFN=%s' % (TestBestman.__hostname, TestBestman.__port, TestBestman.__sfn, TestBestman.__remote_path)
        command = ('srm-rm', srm_url)
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman remove, URL file',
                             status, stdout, stderr)
        file_removed = not os.path.exists(TestBestman.__remote_path)    
        self.assertEqual(status, 0, fail)
        self.assert_(file_removed, 'Copied file still exists') 
        files.remove(TestBestman.__temp_dir) 
