import os
import osgtest.library.core as core
import unittest

class TestStopMySQL(unittest.TestCase):

    def test_01_stop_mysqld(self):
        if not core.rpm_is_installed('mysql-server'):
            core.skip('not installed')
            return
        if core.state['mysql.started-server'] == False:
            core.skip('did not start server')
            return

        command = ('service', 'mysqld', 'stop')
        stdout, stderr, fail = core.check_system(command, 'Stop MySQL')
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(not os.path.exists(core.config['mysql.pid-file']),
                     'MySQL server PID file still exists')
