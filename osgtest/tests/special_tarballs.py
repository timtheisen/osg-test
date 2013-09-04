"""Test cases for the tarball client. These should run in a separate code path
than the regular osg-test tests, since having OSG packages installed into
system locations might interfere with the tarballs.

"""
import glob
import os
import platform
import pwd
import re
import shutil
import tempfile
import unittest
import urllib2

from osgtest.library import core
from osgtest.library import files
from osgtest.library import osgunittest


# TODO These should not be hardcoded
tarball_version = '3.1.22'
tarball_release = '1'
tarball_url_base = 'http://vdt.cs.wisc.edu/tarball-client/'
tarball_metapackage = 'osg-wn-client'

# FIXME switch the directories, obviously
helper_files_dir = '/cloud/login/matyas/osg-test-git/files'
# helper_files_dir = '/usr/share/osg-test'
setup_sh_test_helper = os.path.join(helper_files_dir, 'tarball/setup_sh_test.sh')
setup_csh_test_helper = os.path.join(helper_files_dir, 'tarball/setup_csh_test.csh')

def download(remote_url, dest_filename):
    """Save the file located at 'remote_url' into 'dest_filename'"""
    remote_handle = urllib2.urlopen(remote_url)
    dest_handle = open(dest_filename, 'w')
    try:
        dest_handle.write(remote_handle.read())
    finally:
        dest_handle.close()

class TestTarball(osgunittest.OSGTestCase):
    # unittest creates a new instance of each test case for each test_* method
    # it runs, so I can't use instance variables to store state.
    work_dir = None
    install_dir = None
    install_ok = False

    def get_tarball_filename(self):
        dver = 'el' + str(core.el_release())
        arch = platform.machine()
        return "%s-%s-%s.%s.%s.tar.gz" % (tarball_metapackage, tarball_version, tarball_release, dver, arch)

    def get_tarball_url(self):
        return tarball_url_base + self.get_tarball_filename()

    def assertExists(self, path, message=None):
        if message is None:
            message = path + " does not exist"
        self.assertTrue(os.path.exists(path), message)

    def skip_bad_if_broken_install(self):
        self.skip_bad_if(not TestTarball.install_ok, 'install unsuccessful')

    def skip_ok_if_not_full_client(self):
        self.skip_ok_if(tarball_metapackage == 'osg-wn-client', 'not full client')

    def check_osgrun(self, command, message, exit=0, stdin=None, shell=False):
        """A wrapper around core.check_system to run the given command with
        osgrun as the test user.

        """
        return core.check_system([os.path.join(TestTarball.install_dir, 'osgrun')] + list(command), message, exit=exit, user=True, stdin=stdin, shell=shell)

    def setUp(self):
        """Have each test start in the install dir"""
        if TestTarball.install_dir and os.path.isdir(TestTarball.install_dir):
            os.chdir(TestTarball.install_dir)

    def test_00_init_workdir(self):
        # Create a temp dir to do all our work in.
        # Make sure the test user can write to it.
        TestTarball.work_dir = tempfile.mkdtemp(prefix='tmp-osgtest-tarball')
        uid_of_test_user = pwd.getpwnam(core.options.username).pw_uid
        os.chown(TestTarball.work_dir, uid_of_test_user, -1)
        TestTarball.install_dir = os.path.join(TestTarball.work_dir, tarball_metapackage)

    def test_99_cleanup_workdir(self):
        # Nuke the temp dir
        self.skip_bad_if(not TestTarball.work_dir, 'temp dir not created')
        shutil.rmtree(TestTarball.work_dir)

    def test_01_download_extract_tarball(self):
        # Download tarball from a known location and extract it.
        # TODO: Add way to skip download if we specify an existing tarball on the command line
        self.skip_bad_if(not TestTarball.work_dir, 'no working dir')
        dest_filename = os.path.join(TestTarball.work_dir, self.get_tarball_filename())
        download(self.get_tarball_url(), dest_filename)
        core.check_system(['tar', 'xzf', dest_filename, '-C', TestTarball.work_dir], 'extracting tarball failed', user=True)

    def test_02_osg_post_install(self):
        # Run osg-post-install and verify that it generated the expected files
        self.skip_bad_if(not TestTarball.install_dir or not os.path.exists(TestTarball.install_dir), 'no extracted tarball')
        generated_files = ['setup.csh', 'setup.sh', 'setup-local.csh', 'setup-local.sh', 'osgrun']

        core.check_system(['osg/osg-post-install'], 'cannot run osg-post-install', user=True)
        for gf in generated_files:
            self.assertExists(gf)
        self.assertTrue(os.access('osgrun', os.X_OK), 'osgrun not executable')

        # Now get rid of all of that and run osg-post-install again, but with an argument
        for gf in generated_files:
            os.unlink(gf)

        core.check_system(['osg/osg-post-install', TestTarball.install_dir], 'cannot run osg-post-install', user=True)
        for gf in generated_files:
            self.assertExists(gf)
        self.assertTrue(os.access('osgrun', os.X_OK), 'osgrun not executable')

        TestTarball.install_ok = True

    def test_03_setup_sh(self):
        self.skip_bad_if_broken_install()

        files.write('setup-local.sh', 'export LOCAL_VAR=1\n', backup=False)

        core.check_system([setup_sh_test_helper, TestTarball.install_dir], 'setup.sh test script failed', user=True)

    def test_04_setup_csh(self):
        self.skip_bad_if_broken_install()

        files.write('setup-local.csh', 'setenv LOCAL_VAR 1\n', backup=False)

        core.check_system([setup_csh_test_helper, TestTarball.install_dir], 'setup.csh test script failed', user=True)

    def test_05_grid_proxy_init(self):
        self.skip_bad_if_broken_install()

        password = core.options.password + '\n'
        self.check_osgrun(['grid-proxy-init'], 'grid-proxy-init failed', stdin=password)

    def test_06_osg_ca_manage_setupca(self):
        self.skip_bad_if_broken_install()

        self.check_osgrun(['which', 'osg-ca-manage'], 'osg-ca-manage not in path')
        self.check_osgrun(['osg-ca-manage', 'setupCA', '--url', 'osg'], 'osg-ca-manage setupCA --url osg failed')

        dot0files = glob.glob(os.path.join(TestTarball.install_dir, 'etc/grid-security/certificates/*.0'))

        self.assertTrue(dot0files, 'certificate dir does not contain *.0 files')

    def test_07_voms_proxy_init(self):
        # TODO Implement this
        self.skip_ok_if_not_full_client()

    # Globus tests are going to need the URL of a gatekeeper set up somewhere.
    def test_08_globusrun_a(self):
        # TODO implement this
        self.skip_ok_if_not_full_client()

    def test_09_globus_job_run(self):
        # TODO implement this
        self.skip_ok_if_not_full_client()




if __name__ == '__main__':
    unittest.main()

