import os
from osgtest.library import core, osgunittest
import unittest

class TestStartGridFTP(osgunittest.OSGTestCase):

    def test_01_start_gridftp(self):
        core.config['gridftp.pid-file'] = '/var/run/globus-gridftp-server.pid'
        core.state['gridftp.started-server'] = False

        core.skip_ok_unless_installed('globus-gridftp-server-progs')
        self.skip_ok_if(os.path.exists(core.config['gridftp.pid-file']), 'already running')

        command = ('service', 'globus-gridftp-server', 'start')
        stdout, _, fail = core.check_system(command, 'Start GridFTP server')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(os.path.exists(core.config['gridftp.pid-file']),
                     'GridFTP server PID file missing')
        core.state['gridftp.started-server'] = True
