import os
import re
import shutil
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStartMySQL(osgunittest.OSGTestCase):

    pidfile = '/var/run/mysqld/mysqld.pid'

    def test_01_backup_mysql(self):
        core.skip_ok_unless_installed('mysql-server')

        # If the service is already running, we should stop it
        if os.path.exists(pidfile):
            service.stop('mysqld', sentinel_file=pidfile)

        # Find the folder where the mysql files are stored
        mysql_cfg = files.read('/etc/my.cnf')
        for line in mysql_cfg:
            try:
                core.config['mysql.datadir'] = re.match('datadir=(.*)$', line.strip()).group(1)
            except AttributeError, e:
                if e.args[0] == "'NoneType' object has no attribute 'group'":
                    # No match was found, move onto the next line
                    continue
                else:
                    raise
            else:
                break
        
        # Backup the old mysql folder
        backup = core.config['mysql.datadir'] + '-backup'
        try:
            shutil.move(core.config['mysql.datadir'], backup)
        except OSError:
            # Folder doesn't exist so we don't have to worry about backups
            pass
        else:
            core.config['mysql.backup'] = backup

    def test_02_start_mysqld(self):
        core.skip_ok_unless_installed('mysql-server')
        service.start('mysqld', sentinel_file=pidfile)

