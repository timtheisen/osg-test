import os
import osgtest.library.core as core
import osgtest.library.files as files
import socket
import tempfile
import unittest

class TestXrootd(unittest.TestCase):

    __data_path = '/usr/share/osg-test/test_gridftp_data.txt'

    def test_01_xrdcp_local_to_server(self):
        if core.missing_rpm('xrootd-server', 'xrootd-client'):
            return

        hostname = socket.getfqdn()
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0777)
        xrootd_url = 'root://%s/%s/copied_file.txt' % (hostname, temp_dir)
        command = ('xrdcp', TestXrootd.__data_path , xrootd_url)

        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('xrdcp copy, local to URL',
                             status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir, 'copied_file.txt'))
        files.remove(temp_dir)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_02_xrdcp_server_to_local(self):
        if core.missing_rpm('xrootd-server', 'xrootd-client'):
            return

        hostname = socket.getfqdn()
        temp_source_dir = tempfile.mkdtemp()
        temp_target_dir = tempfile.mkdtemp()
        os.chmod(temp_source_dir, 0777)
        os.chmod(temp_target_dir, 0777)
	f=open(temp_source_dir+"/copied_file.txt","w")
	f.write("This is some test data for an xrootd test.")
	f.close()
        xrootd_url = 'root://%s/%s/copied_file.txt' % (hostname, temp_source_dir)
        local_path = temp_target_dir + '/copied_file.txt'
        command = ('xrdcp', xrootd_url, local_path)

        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Xrootd xrdcp copy, URL to local',
                             status, stdout, stderr)
        file_copied = os.path.exists(local_path)
        files.remove(temp_source_dir)
        files.remove(temp_target_dir)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')
