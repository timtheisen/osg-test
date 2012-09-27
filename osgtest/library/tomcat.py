import os

import osgtest.library.core as core

def majorver():
    "Tomcat major version"
    if core.el_release() > 5:
        return 6
    else:
        return 5

def pkgname():
    "Name of the Tomcat package"
    return "tomcat" + str(majorver())

def datadir():
    "Path of data directory of Tomcat"
    return os.path.join("/usr/share", pkgname())

def logdir():
    "Path of log directory of Tomcat"
    return os.path.join("/var/log", pkgname())

def sysconfdir():
    "Path of config directory of Tomcat (i.e. what is in /etc)"
    return os.path.join("/etc", pkgname())

def conffile():
    "Path of main config file of Tomcat"
    return os.path.join(sysconfdir(), pkgname() + ".conf")

def pidfile():
    "Path of pid file of a running Tomcat"
    return os.path.join("/var/run", pkgname() + ".pid")

def serverlibdir():
    "Path of the server libraries dir of Tomcat"
    if majorver() == 6:
        return os.path.join(datadir(), "lib")
    else:
        return os.path.join(datadir(), "server/lib")

