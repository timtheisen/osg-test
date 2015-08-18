import os
import shutil
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStopMySQL(osgunittest.OSGTestCase):

    def test_01_stop_mysqld(self):
        if not (core.dependency_is_installed('mysql-server')
                or core.dependency_is_installed('mysql-compat-server')):
            self.skip_ok("mysql-server not installed")
        service.stop('mysqld')

    def test_02_restore_backup(self):
        if not core.options.backupmysql:
            return

        core.skip_ok_unless_installed('mysql', by_dependency=True)
        if not (core.dependency_is_installed('mysql-server')
                or core.dependency_is_installed('mysql-compat-server')):
            self.skip_ok("mysql-server not installed")

        if core.config['mysql.backup']:
            files.remove(core.config['mysql.datadir'], force=True)
            shutil.move(core.config['mysql.backup'], core.config['mysql.datadir'])
