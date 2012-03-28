import os
import osgtest.library.core as core
import unittest

class TestStartCondor(unittest.TestCase):

    def test_01_start_condor(self):
        core.config['condor.lockfile'] = '/var/lock/subsys/condor_master'
        core.state['condor.started-service'] = False
        core.state['condor.running-service'] = False

        if core.missing_rpm('condor'):
            return
        if os.path.exists(core.config['condor.lockfile']):
            core.state['condor.running-service'] = True
            core.skip('apparently running')
            return

        command = ('service', 'condor', 'start')
        stdout, _, fail = core.check_system(command, 'Start Condor')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['condor.lockfile']),
                     'Condor run lock file missing')
        core.state['condor.started-service'] = True
        core.state['condor.running-service'] = True
