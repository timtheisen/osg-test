import osgtest.library.core as core
import re
import unittest

class TestNDT(unittest.TestCase):

    def test_01_web100clt(self):
        if core.missing_rpm('ndt'):
            return
        command = ('web100clt', '-v')
        stdout = core.check_system(command, 'NDT client')[0]
        self.assert_(re.search('ndt.+version', stdout, re.IGNORECASE)
                     is not None)
