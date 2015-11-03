import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import socket
import tempfile
import unittest

class TestLCGUtil(osgunittest.OSGTestCase):

    __data_path = '/usr/share/osg-test/test_gridftp_data.txt'
    __port = '10443'
    __sfn = 'srm/v2/server'
    __hostname = socket.getfqdn()


    def setUp(self):
        self.skip_ok_unless(core.state['proxy.created'] or core.state['voms.got-proxy'])
        core.skip_ok_unless_installed('bestman2-server', 'lcg-util')
        self.skip_bad_unless(core.state['bestman.server-running'], 'bestman server not running')

    def get_srm_url_base(self):
        return 'srm://%s:%s/%s?SFN=' % (TestLCGUtil.__hostname, TestLCGUtil.__port, TestLCGUtil.__sfn)

    def get_srm_url(self):
        return self.get_srm_url_base() + TestLCGUtil.__remote_path

    def setup_temp_paths(self):
        TestLCGUtil.__temp_dir = tempfile.mkdtemp()
        TestLCGUtil.__remote_path = TestLCGUtil.__temp_dir + '/lcgutil_put_copied_file.txt'
        TestLCGUtil.__local_path = TestLCGUtil.__temp_dir + '/lcgutil_get_copied_file.txt'

    def test_01_copy_local_to_server_lcg_util(self):
        self.setup_temp_paths()
        os.chmod(TestLCGUtil.__temp_dir, 0777)
        command = ('lcg-cp', '-v', '-b', '-D', 'srmv2', 'file://' + TestLCGUtil.__data_path, self.get_srm_url())
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('lcg-util copy, local to URL', command, status, stdout, stderr)
        file_copied = os.path.exists(TestLCGUtil.__remote_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_02_copy_server_to_local_lcg_util(self):
        command = ('lcg-cp', '-v', '-b', '-D', 'srmv2', self.get_srm_url(), 'file://' + TestLCGUtil.__local_path)
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('lcg-util copy, URL to local', command, status, stdout, stderr)
        file_copied = os.path.exists(TestLCGUtil.__local_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')
        files.remove(TestLCGUtil.__local_path)

    def test_03_remove_server_file_lcg_util(self):
        command = ('lcg-del', '-v', '-b', '-l', '-D', 'srmv2', self.get_srm_url())
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('lcg-util remove, URL file', command, status, stdout, stderr)
        file_removed = not os.path.exists(TestLCGUtil.__remote_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_removed, 'Copied file still exists')
        files.remove(TestLCGUtil.__temp_dir)

