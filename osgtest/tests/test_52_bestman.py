import os
import osgtest.library.core as core
import osgtest.library.files as files
import socket
import tempfile
import unittest

class TestBestman(unittest.TestCase):

    __data_path = '/usr/share/osg-test/test_bestman_data.txt'
    __port = '10443'
    __sfn = 'srm/v2/server'

    def test_01_ping(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client', 'voms-clients'):
           return
        hostname = socket.getfqdn()
        srm_url = 'srm://%s:' % (hostname)
        command = ('srm-ping', srm_url + TestBestman.__port + '/' + TestBestman.__sfn )
        status, stdout, stderr = core.system(command, True)
	fail = core.diagnose('Bestman Ping',
                             status, stdout, stderr)
        self.assertEqual(status, 0, fail) 
 
    """def test_02_copy_local_to_server(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client', 'voms-clients'):
           return

        hostname = socket.getfqdn()
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0777)
        srm_url = 'srm://%s%s/copied_file.txt' % (hostname, temp_dir)
        command = ('srmcp', 'file:///' + TestBestman.__data_path,
                   srm_url)

        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman copy, local to URL',
                             status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir, 'copied_file.txt'))
        files.remove(temp_dir)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_03_copy_server_to_local(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client', 'voms-clients'):     
	   return
        hostname = socket.getfqdn()
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0777)
        srm_url = 'srm://' + hostname + TestBestman.__data_path
        local_path = temp_dir + '/copied_file.txt'
        command = ('srmcp', srm_url, 'file://' + local_path)

        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman copy, URL to local',
                             status, stdout, stderr)
        file_copied = os.path.exists(local_path)
        files.remove(temp_dir)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')"""
