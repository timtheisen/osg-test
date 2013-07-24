import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import unittest

class TestStopCvmfs(osgunittest.OSGTestCase):

    def test_01_stop_cvmfs(self):
        core.skip_ok_unless_installed('cvmfs')
        self.skip_ok_if(['cvmfs.started-server'] == False, 'did not start server')

        if core.state['cvmfs.version'] < ('2', '1'):
            command = ('service', 'cvmfs', 'stop')
        else:
            command = ('cvmfs_config', 'umount')
        stdout, _, fail = core.check_system(command, 'Stop Cvmfs server')
        self.assert_(stdout.find('FAILED') == -1, fail)
        # Restart autofs to bring network filesystems back (specifically
        # homedirs on el5 fermicloud vms)
        if core.state['cvmfs.version'] >= ('2', '1'):
            stdout, _, fail = core.check_system(('service', 'autofs', 'restart'), 'Restart autofs')
            self.assert_(stdout.find('FAILED') == -1, fail)

        files.restore("/etc/fuse.conf","cvmfs")
        files.restore("/etc/auto.master","cvmfs")
        files.restore("/etc/cvmfs/default.local","cvmfs")
        files.restore("/etc/cvmfs/domain.d/cern.ch.local","cvmfs")
