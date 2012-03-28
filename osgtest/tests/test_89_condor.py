import os
import osgtest.library.core as core
import unittest

class TestStopCondor(unittest.TestCase):

    def test_01_stop_condor(self):
        if core.missing_rpm('condor'):
            return
        if core.state['condor.started-service'] == False:
            core.skip('did not start server')
            return

        command = ('service', 'condor', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop Condor')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(not os.path.exists(core.config['condor.lockfile']),
                     'Condor run lock file still present')

        core.state['condor.running-service'] = False
