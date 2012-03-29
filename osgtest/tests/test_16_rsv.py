import os
import osgtest.library.core as core
import unittest

class TestStartRSV(unittest.TestCase):

    def test_01_config(self):
        pass

    def test_02_start_rsv(self):
        core.config['rsv.lockfile'] = "/var/lock/subsys/rsv"
        core.state['rsv.started-service'] = False
        core.state['rsv.running-service'] = False

        if core.missing_rpm('rsv'):
            return

        # Is RSV already running?
        if os.path.exists(core.config['rsv.lockfile']):
            core.state['rsv.running-service'] = True
            core.skip('already running') # skip-ok
            return

        # Before we start RSV, make sure Condor-Cron is up
        if core.state['condor-cron.running-service'] == False:
            core.skip('condor-cron not running') # skip-bad
            return

        command = ('service', 'rsv', 'start')
        stdout, _, fail = core.check_system(command, 'Start RSV')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['rsv.lockfile']),
                     'RSV run lock file missing')

        core.state['rsv.started-service'] = True
        core.state['rsv.running-service'] = True
