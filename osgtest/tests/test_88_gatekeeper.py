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
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Stop Globus gatekeeper', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(stdout.find('FAILED') == -1,
                     "Stopping the Globus gatekeeper reported 'FAILED'")
        self.assert_(not os.path.exists(core.config['globus.gk-lockfile']),
                     'Globus gatekeeper run lock file still present')
