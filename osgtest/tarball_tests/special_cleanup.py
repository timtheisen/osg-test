"""Cleanup for the tarball client tests."""

import shutil

from osgtest.library import core
from osgtest.library import osgunittest

class TestCleanup(osgunittest.OSGTestCase):
    def test_99_cleanup_workdir(self):
        # Nuke the temp dir
        self.skip_bad_if(not core.config['tb_work_dir'], 'temp dir not created')
        shutil.rmtree(core.config['tb_work_dir'])

