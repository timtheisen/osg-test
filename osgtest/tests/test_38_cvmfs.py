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
                self.assertEqual(status, 0, core.diagnose('cvmfs probe', status, stdout, stderr))
            finally:
                files.restore(default_local, 'cvmfsprobe')

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


