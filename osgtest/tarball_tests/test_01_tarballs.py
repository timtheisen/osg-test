"""Test cases for the tarball client. These run in a separate code path
than the regular osg-test tests, since having OSG packages installed into
system locations interferes with the tarballs.

"""
import glob
import os
import re

from osgtest.library import core
from osgtest.library import files
from osgtest.library import osgunittest


helper_files_dir = '/usr/share/osg-test/tarball'
setup_sh_test_helper = os.path.join(helper_files_dir, 'setup_sh_test.sh')
setup_csh_test_helper = os.path.join(helper_files_dir, 'setup_csh_test.csh')

class TestTarball(osgunittest.OSGTestCase):
    # unittest creates a new instance of each test case for each test_* method
    # it runs, so I can't use instance variables to store state.
    install_ok = False
    proxy_ok = False

    def assertExists(self, path, message=None):
        if message is None:
            message = path + " does not exist"
        self.assertTrue(os.path.exists(path), message)

    def skip_bad_if_broken_install(self):
        self.skip_bad_if(not TestTarball.install_ok, 'install unsuccessful')

    def skip_bad_if_no_proxy(self):
        self.skip_bad_if(not TestTarball.proxy_ok, 'no grid proxy')

    def skip_ok_if_not_full_client(self):
        self.skip_ok_if(getattr(core.options, 'tarball_metapackage', '') == 'osg-wn-client', 'not full client')

    def check_osgrun(self, command, message, exit=0, stdin=None, shell=False):
        """A wrapper around core.check_system to run the given command with
        osgrun as the test user.

        """
        return core.check_system([os.path.join(core.config['tb_install_dir'], 'osgrun')] + list(command), message, exit=exit, user=True, stdin=stdin, shell=shell)

    def setUp(self):
        """Have each test start in the install dir"""
        if core.config['tb_install_dir'] and os.path.isdir(core.config['tb_install_dir']):
            os.chdir(core.config['tb_install_dir'])

    def test_01_osg_post_install(self):
        # Run osg-post-install and verify that it generated the expected files
        self.skip_bad_if(not core.config['tb_install_dir'] or not os.path.exists(core.config['tb_install_dir']), 'no extracted tarball')
        generated_files = ['setup.csh', 'setup.sh', 'setup-local.csh', 'setup-local.sh', 'osgrun']

        core.check_system(['osg/osg-post-install'], 'cannot run osg-post-install', user=True)
        for gf in generated_files:
            self.assertExists(gf)
        self.assertTrue(os.access('osgrun', os.X_OK), 'osgrun not executable')

        # Now get rid of all of that and run osg-post-install again, but with an argument
        for gf in generated_files:
            os.unlink(gf)

        core.check_system(['osg/osg-post-install', core.config['tb_install_dir']], 'cannot run osg-post-install', user=True)
        for gf in generated_files:
            self.assertExists(gf)
        self.assertTrue(os.access('osgrun', os.X_OK), 'osgrun not executable')

        TestTarball.install_ok = True

    def test_02_setup_sh(self):
        self.skip_bad_if_broken_install()

        files.write('setup-local.sh', 'export LOCAL_VAR=1\n', backup=False)
        core.check_system([setup_sh_test_helper, core.config['tb_install_dir']], 'setup.sh test script failed', user=True)

    def test_03_setup_csh(self):
        self.skip_bad_if_broken_install()

        files.write('setup-local.csh', 'setenv LOCAL_VAR 1\n', backup=False)
        core.check_system([setup_csh_test_helper, core.config['tb_install_dir']], 'setup.csh test script failed', user=True)

    def test_04_grid_proxy_init(self):
        self.skip_bad_if_broken_install()

        password = core.options.password + '\n'
        self.check_osgrun(['grid-proxy-init'], 'grid-proxy-init failed', stdin=password)

        TestTarball.proxy_ok = True

    def test_05_osg_ca_manage_setupca(self):
        self.skip_bad_if_broken_install()

        self.check_osgrun(['osg-ca-manage', 'setupCA', '--url', 'osg'], 'osg-ca-manage setupCA --url osg failed')
        dot0files = glob.glob(os.path.join(core.config['tb_install_dir'], 'etc/grid-security/certificates/*.0'))
        self.assertTrue(dot0files, 'certificate dir does not contain *.0 files')

    def test_06_voms_proxy_init(self):
        self.skip_ok_if_not_full_client()
        self.skip_ok_unless(hasattr(core.options, 'tarball_vo'), "tarball_vo not specified")
        self.skip_bad_if_broken_install()

        self.check_osgrun(['voms-proxy-init', '-voms', core.options.tarball_vo], 'voms-proxy-init failed')
        self.check_osgrun(['voms-proxy-info'], 'voms-proxy-info failed')

    # Globus tests are going to need the URL of a gatekeeper set up somewhere.
    def test_07_globusrun_a(self):
        self.skip_ok_if_not_full_client()
        self.skip_ok_unless(hasattr(core.options, 'tarball_contact_string'), "tarball_contact_string not specified")
        self.skip_bad_if_broken_install()
        self.skip_bad_if_no_proxy()

        self.check_osgrun(['globusrun', '-a', '-r', core.options.tarball_contact_string], "globusrun -a failed")

    def test_08_globus_job_run(self):
        self.skip_ok_if_not_full_client()
        self.skip_ok_unless(hasattr(core.options, 'tarball_contact_string'), "tarball_contact_string not specified")
        self.skip_bad_if_broken_install()
        self.skip_bad_if_no_proxy()

        self.check_osgrun(['globus-job-run', core.options.tarball_contact_string, '/usr/bin/id'], "globus-job-run failed")

    def test_09_srm_ping(self):
        self.skip_ok_unless(hasattr(core.options, 'tarball_srm_url'), "tarball_srm_url not specified")
        self.skip_bad_if_broken_install()
        self.skip_bad_if_no_proxy()

        self.check_osgrun(['srm-ping', core.options.tarball_srm_url], "srm-ping failed")

