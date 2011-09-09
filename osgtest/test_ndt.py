import osgtest
import re
import unittest

class TestNDT(unittest.TestCase):

    def test_01_web100clt(self):
        if not osgtest.rpm_is_installed('ndt'):
            osgtest.skip()
            return
        (status, stdout, stderr) = osgtest.syspipe(['web100clt', '-v'])
        self.assertEqual(status, 0)
        self.assert_(re.search('ndt.+version', stdout, re.IGNORECASE)
                     is not None)
