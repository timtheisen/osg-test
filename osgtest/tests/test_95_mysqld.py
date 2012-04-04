import os
import unittest

import osgtest.library.core as core
import osgtest.library.service as service

class TestStopMySQL(unittest.TestCase):

    def test_01_stop_mysqld(self):
        if not core.rpm_is_installed('mysql-server'):
            core.skip('not installed')
            return
        service.stop('mysqld')

