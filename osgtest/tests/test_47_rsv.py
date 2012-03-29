import osgtest.library.core as core

import re
import unittest

class TestRSV(unittest.TestCase):

    def start_rsv(self):
        core.check_system(('rsv-control', '--on'), 'rsv-control --on')
        return
    
    def stop_rsv(self):
        core.check_system(('rsv-control', '--off'), 'rsv-control --off')
        return
    
    def config_and_restart(self):
        self.stop_rsv()
        core.check_system(('osg-configure', '-c', '-m', 'rsv'), 'osg-configure -c -m rsv')
        self.start_rsv()
        return


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


    def test_020_start_and_stop(self):
        if core.missing_rpm('rsv'):
            return

        self.stop_rsv()
        self.start_rsv()

    def test_021_job_list(self):
        if core.missing_rpm('rsv'):
            return

        command = ('rsv-control', '--job-list')
        stdout = core.check_system(command, 'rsv-control --job-list')[0]

        # TODO
        # Make sure that the header prints at least.  We can improve this
        self.assert_(re.search('OWNER', stdout) is not None)


        # Check the parsable job-list output
        command = ('rsv-control', '--job-list', '--parsable')
        stdout = core.check_system(command, 'rsv-control --job-list --parsable')[0]

        # The separator is a pipe, so just make sure we got one of those
        self.assert_(re.search('\|', stdout) is not None)

        return
