import os
import osgtest.library.core as core
import unittest

class TestStartXrootd(unittest.TestCase):

    def test_01_start_xrootd(self):
	core.config['xrootd.pid-file']='/var/run/xrootd/xrootd-default.pid'
        core.state['xrootd.started-server'] = False

        if not core.rpm_is_installed('xrootd-server'):
            core.skip('not installed')
            return

        command = ('service', 'xrootd', 'start')
        stdout, stderr, fail = core.check_system(command, 'Start Xrootd server')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(os.path.exists(core.config['xrootd.pid-file']),
                     'xrootd server PID file missing')
        core.state['xrootd.started-server'] = True
