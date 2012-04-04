import os

import osgtest.library.core as core

def majorver():
    if core.el_release() > 5:
        return 6
    else:
        return 5

def pkgname():
    return "tomcat" + str(majorver())

def datadir():
    return os.path.join("/usr/share", pkgname())

def logdir():
    return os.path.join("/var/log", pkgname())

def sysconfdir():
    return os.path.join("/etc", pkgname())

def conffile():
    return os.path.join(sysconfdir(), pkgname() + ".conf")

def pidfile():
    return os.path.join("/var/run", pkgname() + ".pid")

def serverlibdir():
    if majorver() == 6:
        return os.path.join(datadir(), "lib")
    else:
        return os.path.join(datadir(), "server/lib")

