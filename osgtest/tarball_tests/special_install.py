"""Setup for the tarball client tests.

Create a temporary directory to work in, and extract the tarball client into
it. The tarball is taken from the current directory, with the name specified
by the config file.

This uses the following config file entries:

tarball_metapackage (required) -- either osg-wn-client or osg-client
tarball_version -- e.g. 3.1.22.
tarball_release -- e.g. 1.

A glob is used to match the filename -- if tarball_version or tarball_release
are not specified, * is used instead.
"""

import glob
import os
import platform
import pwd
import tempfile

from osgtest.library import core
from osgtest.library import osgunittest


def get_tarball_filename():
    dver = 'el' + str(core.el_release())
    arch = platform.machine()
    filenames = glob.glob("%s-%s-%s.%s.%s.tar.gz" % (core.options.tarball_metapackage, getattr(core.options, 'tarball_version', '*'), getattr(core.options, 'tarball_release', '*'), dver, arch))
    if filenames:
        return filenames[0]
    else:
        return


class TestInstall(osgunittest.OSGTestCase):

    def test_00_init_workdir(self):
        core.config['tb_work_dir'] = core.config['tb_install_dir'] = None
        # Create a temp dir to do all our work in.
        # Make sure the test user can write to it.
        core.config['tb_work_dir'] = tempfile.mkdtemp(prefix='tmp-osgtest-tarball')
        uid_of_test_user = pwd.getpwnam(core.options.username).pw_uid
        os.chown(core.config['tb_work_dir'], uid_of_test_user, -1)
        core.config['tb_install_dir'] = os.path.join(core.config['tb_work_dir'], core.options.tarball_metapackage)

    def test_01_extract_tarball(self):
        tarball = os.path.realpath(get_tarball_filename())
        core.check_system(['tar', 'xzf', tarball, '-C', core.config['tb_work_dir']], 'extracting tarball failed', user=True)

