import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import socket
import shutil
import tempfile
import unittest

class TestCvmfs(osgunittest.OSGTestCase):

    __check_path = '/cvmfs/cms.cern.ch/cmsset_default.sh'

    def test_01_cvmfs_probe(self):
        core.skip_ok_unless_installed('cvmfs', 'cvmfs-keys')

        command = ('cat','/etc/cvmfs/default.local')
        status, stdout, stderr = core.system(command, False)

        if core.state['cvmfs.version'] < ('2', '1'):
            command = ('service','cvmfs', 'probe')
            status, stdout, stderr = core.system(command, False)
        else:
            self.skip_ok('TODO: This test not implemented yet for CVMFS 2.1.X')

    def test_02_cvmfs(self):
        core.skip_ok_unless_installed('cvmfs', 'cvmfs-keys')

        command = ('ls', '/cvmfs')
        status, stdout, stderr = core.system(command, False)
	file_exists = os.path.exists('/cvmfs')
        self.assert_(file_exists, 'Cvmfs mount point missing')

        command = ('ls', '/cvmfs/cms.cern.ch')
        status, stdout, stderr = core.system(command, False)
	file_exists = os.path.exists('/cvmfs/cms.cern.ch')
        self.assert_(file_exists, 'Cvmfs cern mount point missing')

        command = ('ls', self.__check_path)
        status, stdout, stderr = core.system(command, False)
        self.assert_(file_exists, 'Test cvmfs file missing')

        command = ('bash', '-c', 'source ' + self.__check_path)
        status, stdout, stderr = core.system(command, False)
        fail = core.diagnose('cvmfs example source a file on fs',
                             status, stdout, stderr)
        self.assertEqual(status, 0, fail)


