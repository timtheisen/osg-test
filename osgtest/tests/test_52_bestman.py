import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import socket
import tempfile

from osgtest.library.core import osgrelease

class TestBestman(osgunittest.OSGTestCase):

    __data_path = '/usr/share/osg-test/test_gridftp_data.txt'
    __port = '10443'
    __sfn = 'srm/v2/server'
    __hostname = socket.getfqdn()


    @osgrelease(3.3)
    def setUp(self):
        self.skip_ok_unless(core.state['proxy.created'] or core.state['voms.got-proxy'])
        core.skip_ok_unless_installed('bestman2-server', 'bestman2-client', 'gums-service')
        self.skip_bad_unless(core.state['bestman.server-running'], 'bestman server not running')

    def get_srm_url_base(self):
        return 'srm://%s:%s/%s?SFN=' % (TestBestman.__hostname, TestBestman.__port, TestBestman.__sfn)

    def get_srm_url(self):
        return self.get_srm_url_base() + TestBestman.__remote_path

    def setup_temp_paths(self):
        TestBestman.__temp_dir = tempfile.mkdtemp()
        TestBestman.__remote_path = TestBestman.__temp_dir + '/bestman_put_copied_file.txt'
        TestBestman.__local_path = TestBestman.__temp_dir + '/bestman_get_copied_file.txt'

    @osgrelease(3.3)
    def test_01_ping(self):
        command = ('srm-ping', self.get_srm_url_base(), '-debug')
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman Ping', command, status, stdout, stderr)
        self.assertEqual(status, 0, fail) 
 
    @osgrelease(3.3)
    def test_02_copy_local_to_server(self):
        self.setup_temp_paths()
        os.chmod(TestBestman.__temp_dir, 0o777)
        command = ('srm-copy', 'file://' + TestBestman.__data_path, self.get_srm_url(), '-debug')
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman copy, local to URL', command, status, stdout, stderr)
        file_copied = os.path.exists(TestBestman.__remote_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    @osgrelease(3.3)
    def test_03_copy_server_to_local(self):
        command = ('srm-copy', self.get_srm_url(), 'file://' + TestBestman.__local_path, '-debug')
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman copy, URL to local', command, status, stdout, stderr)
        file_copied = os.path.exists(TestBestman.__local_path)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')
        files.remove(TestBestman.__local_path)

    @osgrelease(3.3)
    def test_04_remove_server_file(self):
        command = ('srm-rm', self.get_srm_url(), '-debug')
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('Bestman remove, URL file', command, status, stdout, stderr)
        file_removed = not os.path.exists(TestBestman.__remote_path)    
        self.assertEqual(status, 0, fail)
        self.assert_(file_removed, 'Copied file still exists') 
        files.remove(TestBestman.__temp_dir) 

