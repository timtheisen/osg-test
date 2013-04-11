import os
import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import unittest

class TestStopGridFTP(osgunittest.OSGTestCase):

    def test_01_stop_gridftp(self):
        core.skip_ok_unless_installed('globus-gridftp-server-progs')
        self.skip_ok_if(core.state['gridftp.started-server'] == False, 'did not start server')

        command = ('service', 'globus-gridftp-server', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop GridFTP server')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(not os.path.exists(core.config['gridftp.pid-file']),
                     'GridFTP server PID file still present')
