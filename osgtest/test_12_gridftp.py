import os
import os.path
import osgtest
import shutil
import socket
import tempfile
import unittest

# Must come after the grid-proxy-init test, so that we have a proxy for the
# client commands.

class TestGridFTP(unittest.TestCase):

    __started_server = False
    __pid_file = '/var/run/globus-gridftp-server.pid'

    def test_00_start_gridftp(self):
        TestGridFTP.__started_server = False
        if not osgtest.rpm_is_installed('globus-gridftp-server-progs'):
            osgtest.skip('not installed')
            return
        if os.path.exists(TestGridFTP.__pid_file):
            osgtest.skip('apparently running')
            return

        command = ('service', 'globus-gridftp-server', 'start')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Start GridFTP server', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(stdout.find('FAILED') == -1,
                     "Starting the GridFTP server reported 'FAILED'")
        self.assert_(os.path.exists(TestGridFTP.__pid_file),
                     'GridFTP server PID file missing')
        TestGridFTP.__started_server = True

    def test_01_copy_local_to_server(self):
        if osgtest.missing_rpm('globus-gridftp-server-progs', 'globus-ftp-client',
                               'globus-proxy-utils', 'globus-gass-copy-progs'):
            return

        hostname = socket.getfqdn()
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0777)
        gsiftp_url = 'gsiftp://%s%s/copied_file.txt' % (hostname, temp_dir)
        command = ('globus-url-copy',
                   'file:///usr/share/osg-test/test_gridftp_data.txt',
                   gsiftp_url)

        status, stdout, stderr = osgtest.syspipe(command, True)

        fail = osgtest.diagnose('GridFTP copy, local to URL',
                                status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir, 'copied_file.txt'))
        shutil.rmtree(temp_dir)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_02_copy_server_to_local(self):
        if osgtest.missing_rpm('globus-gridftp-server-progs', 'globus-ftp-client',
                               'globus-proxy-utils', 'globus-gass-copy-progs'):
            return
        hostname = socket.getfqdn()
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0777)
        gsiftp_url = 'gsiftp://' + hostname
        gsiftp_url += '/usr/share/osg-test/test_gridftp_data.txt'
        local_path = temp_dir + '/copied_file.txt'
        command = ('globus-url-copy', gsiftp_url, 'file://' + local_path)
        status, stdout, stderr = osgtest.syspipe(command, True)
        fail = osgtest.diagnose('GridFTP copy, URL to local',
                                status, stdout, stderr)
        file_copied = os.path.exists(local_path)
        shutil.rmtree(temp_dir)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_03_copy_local_to_server_uberftp(self):
        if osgtest.missing_rpm('globus-gridftp-server-progs', 'globus-ftp-client',
                               'globus-proxy-utils', 'globus-gass-copy-progs'):
            return

        hostname = socket.getfqdn()
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0777)

        local_dir  = '/usr/share/osg-test'
        local_path = 'test_gridftp_data.txt'
        ftpCmd = '"cd %s; lcd %s; put %s"' % (temp_dir, local_dir, local_path)
        command = ('uberftp', hostname, ftpCmd)

        status, stdout, stderr = osgtest.syspipe(command, True)
        fail = osgtest.diagnose('UberFTP copy, local to URL',
                                status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir, local_path))

        shutil.rmtree(temp_dir)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_04_copy_server_to_local_uberftp(self):
        if osgtest.missing_rpm('globus-gridftp-server-progs', 'globus-ftp-client',
                               'globus-proxy-utils', 'globus-gass-copy-progs'):
            return

        hostname = socket.getfqdn()
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0777)

        local_dir  = '/usr/share/osg-test'
        local_path = 'test_gridftp_data.txt'
        ftpCmd = '"cd %s; lcd %s; get %s"' % (local_dir, temp_dir, local_path)
        command = ('uberftp', hostname, ftpCmd)

        status, stdout, stderr = osgtest.syspipe(command, True)

        fail = osgtest.diagnose('UberFTP copy, URL to local', status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir, local_path))

        shutil.rmtree(temp_dir)
        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_05_copy_local_to_server_uberftp_parallel(self):
        if osgtest.missing_rpm('globus-gridftp-server-progs', 'globus-ftp-client', 'globus-proxy-utils', 'globus-gass-copy-progs'):
            return

        hostname = socket.getfqdn()

        temp_dir_source = tempfile.mkdtemp()
        temp_dir_dest   = tempfile.mkdtemp()

        os.chmod(temp_dir_source, 0777)
        os.chmod(temp_dir_dest,   0777)

        filename='testfile_10MB'
        full_path = (os.path.join(temp_dir_source, filename))

        command = ('dd', 'if=/dev/zero', 'of='+full_path, 'bs=10485760', 'count=1')
        status, stdout, stderr = osgtest.syspipe(command, True)
        fail = osgtest.diagnose('Creation of a test file using dd', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

        ftpCmd = '"cd %s; lcd %s; put %s"' % (temp_dir_dest, temp_dir_source, filename)
        command = ('uberftp', '-parallel 10', hostname, ftpCmd)

        status, stdout, stderr = osgtest.syspipe(command, True)
        fail = osgtest.diagnose('UberFTP copy, local to URL', status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir_dest, filename))

        shutil.rmtree(temp_dir_source)
        shutil.rmtree(temp_dir_dest)

        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_06_copy_server_to_local_uberftp_parallel(self):
        if osgtest.missing_rpm('globus-gridftp-server-progs', 'globus-ftp-client', 'globus-proxy-utils', 'globus-gass-copy-progs'):
            return

        hostname = socket.getfqdn()

        temp_dir_source = tempfile.mkdtemp()
        temp_dir_dest   = tempfile.mkdtemp()

        os.chmod(temp_dir_source, 0777)
        os.chmod(temp_dir_dest,   0777)

        filename='testfile_10MB'
        full_path = (os.path.join(temp_dir_source, filename))

        command = ('dd', 'if=/dev/zero', 'of='+full_path, 'bs=10485760', 'count=1')
        status, stdout, stderr = osgtest.syspipe(command, True)
        fail = osgtest.diagnose('Creation of a test file using dd', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

        ftpCmd = '"cd %s; lcd %s; get %s"' % (temp_dir_source, temp_dir_dest, filename)
        command = ('uberftp', '-parallel 10', hostname, ftpCmd)

        status, stdout, stderr = osgtest.syspipe(command, True)
        fail = osgtest.diagnose('UberFTP copy, local to URL', status, stdout, stderr)
        file_copied = os.path.exists(os.path.join(temp_dir_dest, filename))

        shutil.rmtree(temp_dir_source)
        shutil.rmtree(temp_dir_dest)

        self.assertEqual(status, 0, fail)
        self.assert_(file_copied, 'Copied file missing')

    def test_99_stop_gridftp(self):
        if not osgtest.rpm_is_installed('globus-gridftp-server-progs'):
            osgtest.skip('not installed')
            return
        if TestGridFTP.__started_server == False:
            osgtest.skip('did not start server')
            return

        command = ('service', 'globus-gridftp-server', 'stop')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Stop GridFTP server', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(stdout.find('FAILED') == -1,
                     "Stopping the GridFTP server reported 'FAILED'")
        self.assert_(not os.path.exists(TestGridFTP.__pid_file),
                     'GridFTP server PID file still present')
