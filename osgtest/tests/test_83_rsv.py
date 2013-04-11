import os
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStopRSV(osgunittest.OSGTestCase):

    def test_01_stop_rsv(self):
        core.skip_ok_unless_installed('rsv')
        self.skip_ok_if(core.state['rsv.started-service'] == False, 'did not start service')

        command = ('service', 'rsv', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop RSV')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(not os.path.exists(core.config['rsv.lockfile']),
                     'RSV run lock file still present')

        core.state['rsv.running-service'] = False

    def test_02_restore_config(self):
        core.skip_ok_unless_installed('rsv')
        files.restore(core.config['system.mapfile'], 'rsv')
