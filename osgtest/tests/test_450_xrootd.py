import os
import socket
import shutil
import tempfile
import pwd

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest


class TestXrootd(osgunittest.OSGTestCase):

    __data_path = '/usr/share/osg-test/test_gridftp_data.txt'
    __fuse_path = '/mnt/xrootd_fuse_test'

    def test_01_xrdcp_local_to_server(self):
        core.skip_ok_unless_installed('xrootd', 'xrootd-client', by_dependency=True)
        if core.config['xrootd.gsi'] == "ON":
            core.skip_ok_unless_installed('globus-proxy-utils')
        self.skip_bad_unless(core.state['xrootd.started-server'] is True, 'Server not running')
        temp_dir = "/tmp/vdttest"
        hostname = socket.getfqdn()
        if core.config['xrootd.gsi'] == "ON":
            if not os.path.exists(temp_dir):
                os.mkdir(temp_dir)
                user = pwd.getpwnam(core.options.username)
                os.chown(temp_dir, user[2], user[3])
        else:
            temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0o777)
        xrootd_url = 'root://%s:%d/%s/copied_file.txt' % (hostname, core.config['xrootd.port'], temp_dir)
        command = ('xrdcp', '--debug', '3', TestXrootd.__data_path, xrootd_url)

        status, stdout, stderr = core.system(command, user=True)

        fail = core.diagnose('xrdcp copy, local to URL',
                             command, status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir, 'copied_file.txt'))
        if core.config['xrootd.multiuser'] != "ON":
            shutil.rmtree(temp_dir)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_02_xrootd_multiuser(self):
        core.skip_ok_unless_installed('xrootd', 'xrootd-client', 'xrootd-multiuser', by_dependency=True)
        temp_dir = "/tmp/vdttest"
        if core.config['xrootd.multiuser'] == "ON":
            file_path = os.path.join(temp_dir, 'copied_file.txt')
            result_perm = core.check_file_ownership(file_path, core.options.username)
            shutil.rmtree(temp_dir)
            self.assertEqual(result_perm, True) 

    def test_03_xrdcp_server_to_local(self):
        core.skip_ok_unless_installed('xrootd', 'xrootd-client', by_dependency=True)
        if core.config['xrootd.gsi'] == "ON":
            core.skip_ok_unless_installed('globus-proxy-utils')
        self.skip_bad_unless(core.state['xrootd.started-server'] is True, 'Server not running')

        hostname = socket.getfqdn()
        temp_source_dir = tempfile.mkdtemp()
        temp_target_dir = tempfile.mkdtemp()
        os.chmod(temp_source_dir, 0o777)
        os.chmod(temp_target_dir, 0o777)
        f = open(temp_source_dir + "/copied_file.txt", "w")
        f.write("This is some test data for an xrootd test.")
        f.close()
        xrootd_url = 'root://%s:%d/%s/copied_file.txt' % (hostname, core.config['xrootd.port'], temp_source_dir)
        local_path = temp_target_dir + '/copied_file.txt'
        command = ('xrdcp', '--debug', '3', xrootd_url, local_path)

        status, stdout, stderr = core.system(command, user=True)

        fail = core.diagnose('Xrootd xrdcp copy, URL to local',
                             command, status, stdout, stderr)
        file_copied = os.path.exists(local_path)
        shutil.rmtree(temp_source_dir)
        shutil.rmtree(temp_target_dir)

        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_04_xrootd_fuse(self):
        # This tests xrootd-fuse using a mount in /mnt
        core.skip_ok_unless_installed('xrootd', 'xrootd-client', 'xrootd-fuse')
        self.skip_ok_unless(os.path.exists("/mnt"), "/mnt did not exist")

        if not os.path.exists(TestXrootd.__fuse_path):
            os.mkdir(TestXrootd.__fuse_path)
        hostname = socket.getfqdn()

        #For some reason, sub process hangs on fuse processes, use os.system
        os.system("mount -t fuse -o rdr=root://localhost:%d//tmp,uid=xrootd xrootdfs %s" %
                  (core.config['xrootd.port'], TestXrootd.__fuse_path))

        # Copy a file in and see if it made it into the fuse mount
        xrootd_url = 'root://%s:%d/%s/copied_file.txt' % (hostname, core.config['xrootd.port'], "/tmp")
        core.system(['xrdcp', '--debug', '3', TestXrootd.__data_path, xrootd_url], user=True)

        self.assert_(os.path.isfile("/tmp/copied_file.txt"), "Test file not uploaded to FUSE mount")

        core.system(['umount', TestXrootd.__fuse_path])
        os.rmdir(TestXrootd.__fuse_path)
        files.remove("/tmp/copied_file.txt")
