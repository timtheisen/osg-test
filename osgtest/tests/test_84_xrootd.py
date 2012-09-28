import os
import osgtest.library.core as core
import osgtest.library.files as files
import unittest

class TestStopXrootd(unittest.TestCase):

    def test_01_stop_xrootd(self):
        if not core.rpm_is_installed('xrootd-server'):
            core.skip('not installed')
            return
        if core.state['xrootd.started-server'] == False:
            core.skip('did not start server')
            return

        command = ('service', 'xrootd', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop Xrootd server')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(not os.path.exists(core.config['xrootd.pid-file']),
                     'Xrootd server PID file still present')
	if core.config['xrootd.gsi'] == "ON":
		files.restore('/etc/xrootd/xrootd-clustered.cfg',"xrootd")
		files.restore('/etc/xrootd/auth_file',"xrootd")
		files.restore('/etc/grid-security/xrd/xrdmapfile',"xrootd")
