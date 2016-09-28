import os

import osgtest.library.core as core

def lockfile_path():
    """The path to the condor lockfile (EL5 and EL6 only)
    Returns None on EL7.

    """
    if core.el_release() >= 7:
        return None

    condor_lockfile = '/var/lock/subsys/condor_master'
    # The name of the lockfile changed in 7.8.8
    if core.rpm_is_installed('condor'):
        condor_version = core.get_package_envra('condor')[2]
        condor_version_split = condor_version.split('.')
        if condor_version_split >= ['7', '8', '8']:
            condor_lockfile = '/var/lock/subsys/condor'
    return condor_lockfile


def wait_for_daemon(collector_log_path, stat, daemon, timeout):
    """Wait until the requested 'daemon' is available and accepting commands by
    monitoring the specified CollectorLog from the position specified by 'stat'
    for a maximum of 'timeout' seconds. Returns True if the daemon becomes
    available within the timeout period and False, otherwise.

    """
    sentinel = r'%sAd\s+:\s+Inserting' % daemon.capitalize()
    return bool(core.monitor_file(collector_log_path, stat, sentinel, timeout)[0])

