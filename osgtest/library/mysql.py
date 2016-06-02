import os
import re

from osgtest.library import core
from osgtest.library import service

def name():
    if core.el_release() < 7:
        return 'mysql'
    else:
        return 'mariadb'

def daemon_name():
    if core.el_release() < 7:
        return 'mysqld'
    else:
        return 'mariadb'

def init_script():
    return daemon_name()

def pidfile():
    return os.path.join('/var/run', daemon_name(), daemon_name() + '.pid')

def server_rpm():
    return name() + '-server'

def client_rpm():
    return name()

def start():
    service.start('mysql', init_script=init_script(), sentinel_file=pidfile())

def stop():
    service.stop('mysql')

def is_running():
    service.is_running('mysql', init_script=init_script())

def _get_command(user='root', database=None):
    command = ['mysql', '-N', '-B', '--user=' + str(user)]
    if database:
        command.append('--database=' + str(database))
    return command

def execute(statements, database=None):
    return core.system(_get_command(database=database), stdin=statements)

def check_execute(statements, message, database=None, exit=0):
    return core.check_system(_get_command(database=database), message, stdin=statements, exit=exit)

def dbdump(destfile, database=None):
    command = "mysqldump --skip-comments --skip-extended-insert -u root "
    if database:
        command += re.escape(database)
    else:
        command += "--all-databases"
    command += ">" + re.escape(destfile)
    core.system(command, user=None, stdin=None, log_output=False, shell=True)
