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

        #TESTING 
        command = ('cat','/etc/cvmfs/default.local')
        status, stdout, stderr = core.system(command, False)
#        command = ('mkdir','-p', '/mnt/testcvmfs')
#        status, stdout, stderr = core.system(command, False)
#        command = ('mount','-t','cvmfs','cms.cern.ch','/mnt/testcvmfs')
#        status, stdout, stderr = core.system(command, False)
#        command = ('ls', '/mnt/testcvmfs')
#        status, stdout, stderr = core.system(command, False)
        command = ('service','cvmfs', 'probe')
        status, stdout, stderr = core.system(command, False)
        #END TESTING

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
        
        command = ('source', self.__check_path)
        status, stdout, stderr = core.system(command, False)
        fail = core.diagnose('cvmfs example source a file on fs',
                             status, stdout, stderr)
        self.assertEqual(status, 0, fail)


