import unittest

import osgtest.library.core as core
import osgtest.library.files as files

class RestoreLcMaps(unittest.TestCase):

    def test_01_restore_lcmaps_after_glexec(self):
        if not core.rpm_is_installed('glexec'):
            core.skip("glexec not installed, don't need lcmaps for it")
            return

        files.restore('/etc/lcmaps.db', 'lcmaps')
