import os
import osgtest.library.core as core
import unittest

class TestStartMySQL(unittest.TestCase):

    def test_01_start_mysqld(self):
        core.config['mysql.pid-file'] = '/var/run/mysqld/mysqld.pid'
        core.state['mysql.started-server'] = False

        if not core.rpm_is_installed('mysql-server'):
            core.skip('not installed')
            return
        if os.path.exists(core.config['mysql.pid-file']):
            core.skip('apparently running')
            return

        command = ('service', 'mysqld', 'start')
        stdout, stderr, fail = core.check_system(command, 'Start MySQL')
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(os.path.exists(core.config['mysql.pid-file']),
                     'MySQL server PID file is missing')
        core.state['mysql.started-server'] = True
