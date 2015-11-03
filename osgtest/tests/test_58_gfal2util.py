import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import socket
import tempfile
import unittest

class TestGFAL2Util(osgunittest.OSGTestCase):

    __data_path = '/usr/share/osg-test/test_gridftp_data.txt'
    __port = '10443'
    __sfn = 'srm/v2/server'
    __hostname = socket.getfqdn()


    def setUp(self):
        self.skip_ok_unless(core.state['proxy.created'] or core.state['voms.got-proxy'])
        core.skip_ok_unless_installed('bestman2-server', 'gfal2-util', 'gfal2-plugin-srm', 'gfal2-plugin-file')
        self.skip_bad_unless(core.state['bestman.server-running'], 'bestman server not running')

    def get_srm_url_base(self):
        return 'srm://%s:%s/%s?SFN=' % (TestGFAL2Util.__hostname, TestGFAL2Util.__port, TestGFAL2Util.__sfn)

    def get_srm_url(self):
        return self.get_srm_url_base() + TestGFAL2Util.__remote_path

    def setup_temp_paths(self):
        TestGFAL2Util.__temp_dir = tempfile.mkdtemp()
        TestGFAL2Util.__remote_path = TestGFAL2Util.__temp_dir + '/gfal2util_put_copied_file.txt'
        TestGFAL2Util.__local_path = TestGFAL2Util.__temp_dir + '/gfal2util_get_copied_file.txt'

    def test_01_copy_local_to_server_gfal2_util(self):
        self.setup_temp_paths()
        os.chmod(TestGFAL2Util.__temp_dir, 0777)
        command = ('gfal-copy', '-v', 'file://' + TestGFAL2Util.__data_path, self.get_srm_url())
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('gfal2-util copy, local to URL', command, status, stdout, stderr)
        file_copied = os.path.exists(TestGFAL2Util.__remote_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_02_copy_server_to_local_gfal2_util(self):
        command = ('gfal-copy', '-v', self.get_srm_url(), 'file://' + TestGFAL2Util.__local_path)
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('gfal2-util copy, URL to local', command, status, stdout, stderr)
        file_copied = os.path.exists(TestGFAL2Util.__local_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')
        files.remove(TestGFAL2Util.__local_path)

    def test_03_remove_server_file_gfal2_util(self):
        command = ('gfal-rm', '-v', self.get_srm_url())
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('gfal2-util remove, URL file', command, status, stdout, stderr)
        file_removed = not os.path.exists(TestGFAL2Util.__remote_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_removed, 'Copied file still exists')
        files.remove(TestGFAL2Util.__temp_dir)

