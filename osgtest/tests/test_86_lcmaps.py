import os
import osgtest.library.core as core
import osgtest.library.files as files
import shutil
import unittest

class RestoreLcMaps(unittest.TestCase):

    # ==================================================================
    def test_01_restore_lcmaps_after_glexec(self):
        if not core.rpm_is_installed('glexec'):
            core.skip("glexec not installed, don't need lcmaps for it")
            return

        path='/etc/lcmaps.db'

        files.restore(path)
