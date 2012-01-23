import os
import osgtest.library.core as core
import unittest

class TestStartGridFTP(unittest.TestCase):

    def test_01_start_gridftp(self):
        core.config['gridftp.pid-file'] = '/var/run/globus-gridftp-server.pid'
        core.state['gridftp.started-server'] = False

        if not core.rpm_is_installed('globus-gridftp-server-progs'):
            core.skip('not installed')
            return
        if os.path.exists(core.config['gridftp.pid-file']):
            core.skip('apparently running')
            return

        command = ('service', 'globus-gridftp-server', 'start')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Start GridFTP server', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(stdout.find('FAILED') == -1,
                     "Starting the GridFTP server reported 'FAILED'")
        self.assert_(os.path.exists(core.config['gridftp.pid-file']),
                     'GridFTP server PID file missing')
        core.state['gridftp.started-server'] = True
