import os
import osgtest.library.core as core
import unittest

class TestStopGridFTP(unittest.TestCase):

    def test_01_stop_gridftp(self):
        if not core.rpm_is_installed('globus-gridftp-server-progs'):
            core.skip('not installed')
            return
        if core.state['gridftp.started-server'] == False:
            core.skip('did not start server')
            return

        command = ('service', 'globus-gridftp-server', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop GridFTP server')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(not os.path.exists(core.config['gridftp.pid-file']),
                     'GridFTP server PID file still present')
