import os
import unittest

import osgtest.library.core as core
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStartMySQL(osgunittest.OSGTestCase):

    def test_01_start_mysqld(self):
        core.skip_ok_unless_installed('mysql-server')
        service.start('mysqld', sentinel_file='/var/run/mysqld/mysqld.pid')

