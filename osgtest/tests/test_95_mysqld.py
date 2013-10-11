import os
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStopMySQL(osgunittest.OSGTestCase):

    def test_01_stop_mysqld(self):
        core.skip_ok_unless_installed('mysql-server')
        service.stop('mysqld')

    def test_02_restore_backup(self):
        core.skip_ok_unless_installed('mysql-server')

        files.remove(core.config['mysql.datadir'], force=True)

        try:
            shutil.move(backup, core.config['mysql.backup'])
        except KeyError:
            # Backup was never created
            pass
