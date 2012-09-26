import os
import osgtest.library.core as core
import unittest
import tempfile

class TestFetchUrl(unittest.TestCase):
    def test_01_fetch_url(self):
        if core.missing_rpm('fetch-crl'):
            return
        command=['fetch-crl']
        stdout, _, fail = core.check_system(command, 'Start fetch-crl')
        count=0
        for name in os.listdir("/etc/grid-security/certificates"):
            if name[-2:] == "r0":
                count=count+1
        self.assert_(count>3,True)
    def test_02_fetch_url_dir(self):
        if core.missing_rpm('fetch-crl'):
            return
        tmpdir=tempfile.mkdtemp()
        command=('fetch-crl','-o',tmpdir)
        stdout, _, fail = core.check_system(command, 'Start fetch-crl with a output dir')
        count=0
        for name in os.listdir(tmpdir):
            if name[-2:] == "r0":
                count=count+1
            os.unlink(os.path.join(tmpdir,name))
        os.rmdir(tmpdir)
        self.assert_(count>3,True)
        
