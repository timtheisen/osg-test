import os

import osgtest.library.core as core

def pkgname():
    "Name of the Tomcat package"
    if core.el_release() == 6:
        return "tomcat6"
    else:
        return "tomcat"

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

def contextfile():
    "Path of main context.xml file of Tomcat"
    return os.path.join(sysconfdir(), 'context.xml')

def catalinafile():
    "Path of Catalina log file that contains the startup sentinel"
    if pkgname() == "tomcat6":
        return os.path.join(logdir(), 'catalina.out')
    else:
        return os.path.join(logdir(), 'catalina.log')

def pidfile():
    "Path of pid file of a running Tomcat"
    return os.path.join("/var/run", pkgname() + ".pid")

def serverlibdir():
    "Path of the server libraries dir of Tomcat"
    return os.path.join(datadir(), "lib")

