import os
import unittest

import osgtest.library.core as core
import osgtest.library.files as files

class TestStopRSV(unittest.TestCase):

    def test_01_stop_rsv(self):
        if core.missing_rpm('rsv'):
            return
        if core.state['rsv.started-service'] == False:
            core.skip('did not start service')
            return

        command = ('service', 'rsv', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop RSV')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(not os.path.exists(core.config['rsv.lockfile']),
                     'RSV run lock file still present')

        core.state['rsv.running-service'] = False

    def test_02_restore_config(self):
        if core.missing_rpm('rsv'):
            return
        files.restore(core.config['system.mapfile'], 'rsv')
