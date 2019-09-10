import os
import pwd
import shutil
import socket
import tempfile

from osgtest.library import core
from osgtest.library import osgunittest


SOURCE_PATH = '/usr/share/osg-test/test_gridftp_data.txt'


class TestGSIOpenSSH(osgunittest.OSGTestCase):
    hostname = socket.getfqdn()
    temp_dir = None
    remote_path = None
    local_path = None
    port = None

    def setUp(self):
        core.skip_ok_unless_installed('gsi-openssh-server', 'gsi-openssh-clients')
        self.skip_ok_unless(core.state['gsisshd.can-run'], "Couldn't run gsisshd (see above)")
        self.skip_ok_unless(core.state['proxy.valid'] or core.state['voms.got-proxy'], 'no proxy')
        self.skip_bad_unless(core.state['gsisshd.started-service'], 'gsisshd service not running')
        self.port = core.config['gsisshd.port']

    def test_00_setup(self):
        if not TestGSIOpenSSH.temp_dir or not os.path.isdir(TestGSIOpenSSH.temp_dir):
            TestGSIOpenSSH.temp_dir = tempfile.mkdtemp()
            uid, gid = pwd.getpwnam(core.options.username)[2:4]
            os.chown(TestGSIOpenSSH.temp_dir, uid, gid)
            TestGSIOpenSSH.remote_path = TestGSIOpenSSH.temp_dir + '/gsissh_put_copied_file.txt'
            TestGSIOpenSSH.local_path = TestGSIOpenSSH.temp_dir + '/gsissh_get_copied_file.txt'

    def test_01_ssh_to_host(self):
        command = ['gsissh', '-p', self.port, self.hostname, 'echo', 'SUCCESS']
        stdout, _, fail = core.check_system(command, 'SSH to host', user=True, stdin="")

        self.assert_('SUCCESS' in stdout, fail)

    def test_02_scp_local_to_remote(self):
        command = ['gsiscp', '-P', self.port, SOURCE_PATH, self.hostname + ':' + self.remote_path]
        stdout, _, fail = core.check_system(command, 'SCP to host', user=True, stdin="")

        self.assert_(os.path.exists(self.remote_path), 'Copied file missing')

    def test_03_scp_remote_to_local(self):
        command = ['gsiscp', '-P', self.port, self.hostname + ':' + self.remote_path, self.local_path]
        stdout, _, fail = core.check_system(command, 'SCP from host', user=True, stdin="")

        self.assert_(os.path.exists(self.local_path), 'Copied file missing')

    def test_99_cleanup(self):
        shutil.rmtree(TestGSIOpenSSH.temp_dir)

