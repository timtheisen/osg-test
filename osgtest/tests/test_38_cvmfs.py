import os
import osgtest.library.core as core
import osgtest.library.files as files
import socket
import shutil
import tempfile
import unittest

class TestCvmfs(unittest.TestCase):

    __check_path = '/cvmfs/cms.cern.ch/cmsset_default.sh'

    def test_01_cvmfs(self):
        if core.missing_rpm('cvmfs', 'cvmfs-keys'):
            return

        command = ('ls', self.__check_path)
        status, stdout, stderr = core.system(command, True)

        file_exists = os.path.exists(self.__check_path)
        self.assert_(file_exists, 'Test cvmfs file missing')
        
        command = ('source', self.__check_path)
        status, stdout, stderr = core.system(command, True)
        fail = core.diagnose('cvmfs example source a file on fs',
                             status, stdout, stderr)
        self.assertEqual(status, 0, fail)


