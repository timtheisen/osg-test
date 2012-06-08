import os
import osgtest.library.core as core
import osgtest.library.files as files
import unittest

class TestStopCvmfs(unittest.TestCase):

    def test_01_stop_xrootd(self):
        if not core.rpm_is_installed('cvmfs'):
            core.skip('not installed')
            return
        if core.state['cvmfs.started-server'] == False:
            core.skip('did not start server')
            return

        command = ('service', 'cvmfs', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop Cvmfs server')
        self.assert_(stdout.find('FAILED') == -1, fail)

	files.restore("/etc/fuse.conf","root")
	files.restore("/etc/auto.master","root")
	files.restore("/etc/cvmfs/default.local","root")
