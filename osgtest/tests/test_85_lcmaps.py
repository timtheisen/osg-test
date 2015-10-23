import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestRestoreLcMaps(osgunittest.OSGTestCase):

    def test_01_restore_lcmaps_after_glexec(self):
        core.skip_ok_unless_installed('glexec')

        files.restore('/etc/lcmaps.db', 'lcmaps')
