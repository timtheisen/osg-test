import os
import unittest

from osgtest.library import core, osgunittest

class TestStartRSV(osgunittest.OSGTestCase):

    def test_01_config(self):
        pass

    def test_02_start_rsv(self):
        core.config['rsv.lockfile'] = "/var/lock/subsys/rsv"
        core.state['rsv.started-service'] = False
        core.state['rsv.running-service'] = False

        core.skip_ok_unless_installed('rsv')

        # Is RSV already running?
        if os.path.exists(core.config['rsv.lockfile']):
            core.state['rsv.running-service'] = True
            self.skip_ok('already running')

        # Before we start RSV, make sure Condor-Cron is up
        self.skip_bad_unless(core.state['condor-cron.running-service'], 'Condor-Cron not running')

        command = ('service', 'rsv', 'start')
        stdout, _, fail = core.check_system(command, 'Start RSV')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['rsv.lockfile']),
                     'RSV run lock file missing')

        core.state['rsv.started-service'] = True
        core.state['rsv.running-service'] = True
