import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import tempfile

class TestSingularity(osgunittest.OSGTestCase):

    __check_path = '/cvmfs/cms.cern.ch/cmsset_default.sh'
    __cvfms_image = '/cvmfs/singularity.opensciencegrid.org/opensciencegrid/osg-wn:3.3-el6 cat /etc/redhat-release'
    core.config['cvmfs.debug-dirs'] = []

    def test_01_singularity(self):
        core.skip_ok_unless_installed('singularity-runtime')
        core.skip_ok_unless_installed('cvmfs')
        core.skip_ok_unless_installed('cvmfs-keys', by_dependency=True)
        core.state['cvmfs.mounted'] = False

        command = ('ls', '/cvmfs')
        status, stdout, stderr = core.system(command, False)
        file_exists = os.path.exists('/cvmfs')
        self.assert_(file_exists, 'Cvmfs mount point missing')
        core.state['cvmfs.mounted'] = True

        singularity_repo = 'singularity.opensciencegrid.org'
        command = ('ls', '/cvmfs/' + singularity_repo)
        status, stdout, stderr = core.system(command, False)

        # If the previous command failed, output better debug info
        if status != 0:
            self.debug_cvmfs(singularity_repo)

        command = ('ls', self.__cvmfs_image)
        status, stdout, stderr = core.system(command, False)
        self.assert_(file_exists, 'cvfms image missing')
        
        #command = ('bash', '-c', 'source ' + self.__check_path)
        #command = "singularity exec --containall --bind /cvmfs --home $HOME:/srv /cvmfs/singularity.opensciencegrid.org/opensciencegrid/osg-wn:3.3-el6 cat /etc/redhat-release"
        command= ('singularity', 'exec', '--containall', '--bind', 'cvmfs', self.__cvmfs_image, 'cat', '/etc/redhat-release')
        status, stdout, stderr = core.system(command, False)
        fail = core.diagnose('singularity checking a file',
                             command, status, stdout, stderr)
        self.assertEqual(status, 0, fail)
