import os

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
