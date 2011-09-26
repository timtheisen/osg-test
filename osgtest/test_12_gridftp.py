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

    def test_00_start_gridftp(self):
        TestGridFTP.__started_server = False
        if not osgtest.rpm_is_installed('globus-gridftp-server-progs'):
            osgtest.skip('not installed')
            return
        if os.path.exists('/var/lock/subsys/globus-gridftp-server'):
            osgtest.skip('apparently running')
            return

        command = ['service', 'globus-gridftp-server', 'start']
        (status, stdout, stderr) = osgtest.syspipe(command)
        self.assertEqual(status, 0, "Starting the GridFTP server failed with "
                         "exit status %d" % status)
        self.assert_(stdout.find('FAILED') == -1,
                     "Starting the GridFTP server reported 'FAILED'")
        self.assert_(os.path.exists('/var/lock/subsys/globus-gridftp-server'),
                     'GridFTP server run lock file missing')
        TestGridFTP.__started_server = True

    def test_01_copy_local_to_server(self):
        if osgtest.missing_rpm(['globus-gridftp-server-progs', 'globus-ftp-client',
                                'globus-proxy-utils', 'globus-gass-copy-progs']):
            return
        hostname = socket.getfqdn()
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0777)
        gsiftp_url = 'gsiftp://%s%s/copied_file.txt' % (hostname, temp_dir)
        command = ['globus-url-copy',
                   'file:///usr/share/osg-test/test_gridftp_data.txt',
                   gsiftp_url]
        (status, stdout, stderr) = osgtest.syspipe(command, True)
        file_copied = os.path.exists(os.path.join(temp_dir, 'copied_file.txt'))
        shutil.rmtree(temp_dir)
        self.assertEqual(status, 0,
                         'File copy failed with exit status %d' % status)
        self.assert_(file_copied, 'Copied file missing')

    def test_02_copy_server_to_local(self):
        if osgtest.missing_rpm(['globus-gridftp-server-progs', 'globus-ftp-client',
                                'globus-proxy-utils', 'globus-gass-copy-progs']):
            return
        hostname = socket.getfqdn()
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0777)
        gsiftp_url = 'gsiftp://' + hostname
        gsiftp_url += '/usr/share/osg-test/test_gridftp_data.txt'
        local_path = temp_dir + '/copied_file.txt'
        command = ['globus-url-copy', gsiftp_url, 'file://' + local_path]
        (status, stdout, stderr) = osgtest.syspipe(command, True)
        file_copied = os.path.exists(local_path)
        shutil.rmtree(temp_dir)
        self.assertEqual(status, 0,
                         'File copy failed with exit status %d' % status)
        self.assert_(file_copied, 'Copied file missing')

    def test_99_stop_gridftp(self):
        if not osgtest.rpm_is_installed('globus-gridftp-server-progs'):
            osgtest.skip('not installed')
            return
        if TestGridFTP.__started_server == False:
            osgtest.skip('did not start server')
            return

        command = ['service', 'globus-gridftp-server', 'stop']
        (status, stdout, stderr) = osgtest.syspipe(command)
        self.assertEqual(status, 0, "Stopping the GridFTP server failed with "
                         "exit status %d" % status)
        self.assert_(stdout.find('FAILED') == -1,
                     "Stopping the GridFTP server reported 'FAILED'")
        self.assert_(not
                     os.path.exists('/var/lock/subsys/globus-gridftp-server'),
                     'GridFTP server run lock file still present')
