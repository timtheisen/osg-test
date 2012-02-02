import os
import osgtest.library.core as core
import unittest

class TestStopGatekeeper(unittest.TestCase):

    def test_01_stop_gatekeeper(self):
        if not core.rpm_is_installed('globus-gatekeeper'):
            core.skip('not installed')
            return
        if core.state['globus.started-gk'] == False:
            core.skip('did not start server')
            return

        command = ('service', 'globus-gatekeeper', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop Globus gatekeeper')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(not os.path.exists(core.config['globus.gk-lockfile']),
                     'Globus gatekeeper run lock file still present')
