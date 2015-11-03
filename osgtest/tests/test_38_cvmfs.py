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
    core.config['cvmfs.debug-dirs'] = []

    def debug_cvmfs(self, repo):
        temp_dir = tempfile.mkdtemp()
        core.config['cvmfs.debug-dirs'].append(temp_dir)
        command = ('mount', '-t', 'cvmfs', repo, temp_dir)
        core.check_system(command, 'Manual cvmfs mount failed')
        # If manual mount works, autofs is broken
        self.assert_(False, "Autofs failed to mount /cvmfs/%s" % repo)

    def test_01_cvmfs_probe(self):
        default_local = '/etc/cvmfs/default.local'
        probe_repos = ",".join([
            'atlas.cern.ch',
            'cms.cern.ch',
            'oasis.opensciencegrid.org'])
        # Test depends on oasis-config to access the oasis.opensciencegrid.org
        # repo. This is an external service, so the requirement should be
        # removed as part of SOFTWARE-1108.
        core.skip_ok_unless_installed('cvmfs', 'cvmfs-keys', 'oasis-config')


        command = ('cat', default_local)
        status, stdout, stderr = core.system(command, False)

        if core.state['cvmfs.version'] < ('2', '1'):
            command = ('service','cvmfs', 'probe')
            status, stdout, stderr = core.system(command, False)
        else:
            # Dave Dykstra suggested running cvmfs probe against a different
            # set of repositories than are currently set up, so we modify them
            # just for this test. (See SOFTWARE-1097)

            # In the future, this test might be removed since we do not want
            # to depend on external services, and it's redundant to probe the
            # repos that we have already mounted.
            files.replace(
                default_local,
                'CVMFS_REPOSITORIES=cms.cern.ch',
                'CVMFS_REPOSITORIES=' + probe_repos,
                owner='cvmfsprobe')
            try:
                command = ('cvmfs_config', 'probe')
                status, stdout, stderr = core.system(command, False)
                self.assertEqual(status, 0, core.diagnose('cvmfs probe', command, status, stdout, stderr))
            finally:
                files.restore(default_local, 'cvmfsprobe')

    def test_02_cvmfs(self):
        core.skip_ok_unless_installed('cvmfs', 'cvmfs-keys')
        core.state['cvmfs.mounted'] = False

        command = ('ls', '/cvmfs')
        status, stdout, stderr = core.system(command, False)
	file_exists = os.path.exists('/cvmfs')
        self.assert_(file_exists, 'Cvmfs mount point missing')
        core.state['cvmfs.mounted'] = True

        cern_repo = 'cms.cern.ch'
        command = ('ls', '/cvmfs/' + cern_repo)
        status, stdout, stderr = core.system(command, False)

        # If the previous command failed, output better debug info
        if status != 0:
            self.debug_cvmfs(cern_repo)

        command = ('ls', self.__check_path)
        status, stdout, stderr = core.system(command, False)
        self.assert_(file_exists, 'Test cvmfs file missing')

        command = ('bash', '-c', 'source ' + self.__check_path)
        status, stdout, stderr = core.system(command, False)
        fail = core.diagnose('cvmfs example source a file on fs',
                             command, status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    def test_03_oasis_config(self):
        core.skip_ok_unless_installed('cvmfs', 'cvmfs-keys', 'oasis-config')
        self.skip_bad_unless(core.state['cvmfs.mounted'], 'Cvmfs mount point missing')

        oasis_repo = 'oasis.opensciencegrid.org'
        command = ('ls', '/cvmfs/' + oasis_repo)
        status, stdout, stderr = core.system(command, False)

        # If the previous command failed, output better debug info
        if status != 0:
            self.debug_cvmfs(oasis_repo)
