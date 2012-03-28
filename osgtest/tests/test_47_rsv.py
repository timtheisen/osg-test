import osgtest.library.core as core

import re
import unittest

class TestRSV(unittest.TestCase):

    def test_001_version(self):
        if core.missing_rpm('rsv'):
            return

        command = ('rsv-control', '--version')
        stdout = core.check_system(command, 'rsv-control --version')[0]

        # The rsv-control --version just returns a string like '1.0.0'.
        self.assert_(re.search('\d.\d.\d', stdout) is not None)


    def test_010_list(self):
        if core.missing_rpm('rsv'):
            return

        command = ('rsv-control', '--list', '--all')
        stdout = core.check_system(command, 'rsv-control --list --all')[0]

        # I don't want to parse the output too much, but we know that most
        # of the metrics start with 'org.osg.'.  So just check for that string
        # once and we'll call it good enough.
        self.assert_(re.search('org.osg.', stdout) is not None)

    def test_011_list_with_cron(self):
        if core.missing_rpm('rsv'):
            return
        
        command = ('rsv-control', '--list', '--all', '--cron')
        stdout = core.check_system(command, 'rsv-control --list --all')[0]

        # One of the header columns will say 'Cron times'
        self.assert_(re.search('Cron times', stdout) is not None)
