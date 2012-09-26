import os
import os.path
import osgtest.library.core as core
import osgtest.library.files as files
import socket
import shutil
import tempfile
import unittest

class TestUberFTP(unittest.TestCase):

    def test_01_copy_local_to_server_uberftp(self):
        if core.missing_rpm('globus-gridftp-server-progs', 'globus-ftp-client',
                            'globus-proxy-utils', 'globus-gass-copy-progs',
                            'uberftp'):
            return
        hostname = socket.getfqdn()
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0777)
        local_dir  = '/usr/share/osg-test'
        local_path = 'test_gridftp_data.txt'
        ftp_cmd = 'cd %s; lcd %s; put %s' % (temp_dir, local_dir, local_path)
        command = ('uberftp', hostname, ftp_cmd)

        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('UberFTP copy, local to URL',
                             status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir, local_path))
        shutil.rmtree(temp_dir)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_02_copy_server_to_local_uberftp(self):
        if core.missing_rpm('globus-gridftp-server-progs', 'globus-ftp-client',
                            'globus-proxy-utils', 'globus-gass-copy-progs',
                            'uberftp'):
            return

        hostname = socket.getfqdn()
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0777)
        local_dir  = '/usr/share/osg-test'
        local_path = 'test_gridftp_data.txt'
        ftp_cmd = 'cd %s; lcd %s; get %s' % (local_dir, temp_dir, local_path)
        command = ('uberftp', hostname, ftp_cmd)

        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('UberFTP copy, URL to local',
                             status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir, local_path))
        shutil.rmtree(temp_dir)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_03_copy_local_to_server_uberftp_parallel(self):
        if core.missing_rpm('globus-gridftp-server-progs', 'globus-ftp-client',
                            'globus-proxy-utils', 'globus-gass-copy-progs',
                            'uberftp'):
            return

        hostname = socket.getfqdn()
        temp_dir_source = tempfile.mkdtemp()
        temp_dir_dest = tempfile.mkdtemp()
        os.chmod(temp_dir_source, 0777)
        os.chmod(temp_dir_dest, 0777)
        filename = 'testfile_10MB'
        full_path = os.path.join(temp_dir_source, filename)
        command = ('dd', 'if=/dev/zero', 'of=' + full_path, 'bs=10485760',
                   'count=1')
        core.check_system(command, 'Create test file with dd', user=True)

        ftp_cmd = ('cd %s; lcd %s; put %s' %
                   (temp_dir_dest, temp_dir_source, filename))
        command = ('uberftp', '-parallel', '10', hostname, ftp_cmd)
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('UberFTP copy, local to URL',
                             status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir_dest, filename))
        shutil.rmtree(temp_dir_source)
        shutil.rmtree(temp_dir_dest)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_04_copy_server_to_local_uberftp_parallel(self):
        if core.missing_rpm('globus-gridftp-server-progs', 'globus-ftp-client',
                            'globus-proxy-utils', 'globus-gass-copy-progs',
                            'uberftp'):
            return

        hostname = socket.getfqdn()
        temp_dir_source = tempfile.mkdtemp()
        temp_dir_dest = tempfile.mkdtemp()
        os.chmod(temp_dir_source, 0777)
        os.chmod(temp_dir_dest, 0777)
        filename = 'testfile_10MB'
        full_path = (os.path.join(temp_dir_source, filename))
        command = ('dd', 'if=/dev/zero', 'of=' + full_path, 'bs=10485760',
                   'count=1')
        core.check_system(command, 'Create test file with dd', user=True)

        ftp_cmd = ('cd %s; lcd %s; get %s' %
                   (temp_dir_source, temp_dir_dest, filename))
        command = ('uberftp', '-parallel','10', hostname, ftp_cmd)
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('UberFTP copy, local to URL',
                             status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir_dest, filename))
        shutil.rmtree(temp_dir_source)
        shutil.rmtree(temp_dir_dest)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')
