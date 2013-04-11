import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import unittest

class TestStopCvmfs(osgunittest.OSGTestCase):

    def test_01_stop_xrootd(self):
        core.skip_ok_unless_installed('cvmfs')
        self.skip_ok_if(['cvmfs.started-server'] == False, 'did not start server')

        command = ('service', 'cvmfs', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop Cvmfs server')
        self.assert_(stdout.find('FAILED') == -1, fail)

        files.restore("/etc/fuse.conf","root")
        files.restore("/etc/auto.master","root")
        files.restore("/etc/cvmfs/default.local","root")
        files.restore("/etc/cvmfs/domain.d/cern.ch.local","root")
