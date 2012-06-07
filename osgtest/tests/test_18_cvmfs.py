import os
import osgtest.library.core as core
import osgtest.library.files as files
import unittest

class TestStartCvmfs(unittest.TestCase):

    def setup_fuse(self):
	fuse_conf_path='/etc/fuse.conf'
        try:
	    contents = files.read(fuse_conf_path)
        except IOError:
            #Sometimes this file doesn't exist
            contents=[]
        for line in contents:
            if "user_allow_other" in line:
                return
        contents.append("user_allow_other\n")
        files.write(fuse_conf_path, contents)
        os.chmod(fuse_conf_path,0644)
       
    def setup_automount(self):
	automount_conf_path='/etc/auto.master'
        try:
	    contents = files.read(automount_conf_path)
        except IOError:
            #Sometimes this file doesn't exist
            contents=[]
        for line in contents:
            if "cvmfs" in line:
                return
        contents.append("/cvmfs /etc/auto.cvmfs\n")
        files.write(automount_conf_path, contents)
        os.chmod(automount_conf_path,0644)
    
    def setup_cvmfs(self):
        contents=[]
        contents.append("CVMFS_REPOSITORIES=cms.cern.ch\n")
        contents.append("CVMFS_CACHE_BASE=/var/scratch/cvmfs\n")
        contents.append("CVMFS_QUOTA_LIMIT=10000\n")
        contents.append("CVMFS_HTTP_PROXY=\"http://cmsfrontier1.fnal.gov:3128\"\n")
        files.write("/etc/cvmfs/default.local", contents)
        os.chmod("/etc/cvmfs/default.local",0644)
	
    def test_01_setup_cvmfs(self):
        self.setup_fuse()
        self.setup_automount()
        self.setup_cvmfs()

    def test_02_start_cvmfs(self):
        core.state['cvmfs.started-server'] = False

        if not core.rpm_is_installed('cvmfs'):
            core.skip('not installed')
            return

        command = ('service', 'cvmfs', 'restartautofs')
        stdout, stderr, fail = core.check_system(command, 'Start cvmfs server')
        self.assert_(stdout.find('FAILED') == -1, fail)
        core.state['cvmfs.started-server'] = True
