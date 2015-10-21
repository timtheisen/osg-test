import os
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStopBestman(osgunittest.OSGTestCase):

    def test_01_stop_bestman(self):
        core.skip_ok_unless_installed('bestman2-server', 'bestman2-client')
        self.skip_ok_unless(core.state['bestman.started-server'], 'bestman server not started')
        command = ('service', 'bestman2', 'stop')
        stdout, _, fail = core.check_system(command, 'Shutting down bestman2')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(not os.path.exists(core.config['bestman.pid-file']),
                     'Bestman server PID file still present')

    def test_02_deconfig_sudoers(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client'):
            return
        files.restore('/etc/sudoers', 'bestman')
