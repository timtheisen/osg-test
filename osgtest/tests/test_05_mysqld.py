import os
import unittest

import osgtest.library.core as core
import osgtest.library.service as service

class TestStartMySQL(unittest.TestCase):

    def test_01_start_mysqld(self):
        if not core.rpm_is_installed('mysql-server'):
            core.skip('not installed')
            return
        service.start('mysqld', sentinel_file='/var/run/mysqld/mysqld.pid')

