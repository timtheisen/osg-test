import os
import osgtest.library.core as core
import unittest

class TestStopCondor(unittest.TestCase):

    def test_01_stop_condor(self):
        if not core.rpm_is_installed('condor'):
            core.skip('not installed')
            return
        if core.state['condor.started-master'] == False:
            core.skip('did not start server')
            return

        command = ('service', 'condor', 'stop')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Stop Condor', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(stdout.find('error') == -1,
                     "Stopping Condor reported 'error'")
        self.assert_(not os.path.exists(core.config['condor.lockfile']),
                     'Condor run lock file still present')
