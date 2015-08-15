import os
import re
import shutil
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStartMySQL(osgunittest.OSGTestCase):


    def test_01_backup_mysql(self):
        if not core.options.backupmysql:
            return

        core.skip_ok_unless_installed('mysql-server', 'mysql', by_dependency=True)
        core.config['mysql.datadir'] = None
        core.config['mysql.backup'] = None
        
        # Find the folder where the mysql files are stored
        pidfile = '/var/run/mysqld/mysqld.pid'
        if not os.path.exists(pidfile):
            service.start('mysqld', sentinel_file=pidfile) # Need mysql up to determine its datadir

        command = ('mysql', '-sNe', "SHOW VARIABLES where Variable_name='datadir';")
        mysql_cfg = core.check_system(command, 'dump mysql config')[0]
        core.config['mysql.datadir'] = re.match('datadir\s*(.+?)\/\s*$', mysql_cfg).group(1)
        self.assert_(core.config['mysql.datadir'] is not None, 'could not extract MySQL datadir')

        # Backup the old mysql folder
        service.stop('mysqld') 
        backup = core.config['mysql.datadir'] + '-backup'
        self.assert_(not os.path.exists(backup), 'mysql-backup already exists')
        try:
            shutil.move(core.config['mysql.datadir'], backup)
        except IOError, e:
            if e.errno == 2:
                # Folder doesn't exist so we don't have to worry about backups
                pass
        else:
            core.config['mysql.backup'] = backup

    def test_02_start_mysqld(self):
        core.skip_ok_unless_installed('mysql-server', by_dependency=True)
        service.start('mysqld', sentinel_file='/var/run/mysqld/mysqld.pid')

