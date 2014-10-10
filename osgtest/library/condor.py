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


def is_running():
    """True if condor is running, False otherwise
    On EL5 and EL6, tests the existence of a lockfile. On EL7, runs
    'service condor status'

    """
    condor_lockfile = lockfile_path()
    if condor_lockfile is not None:
        return os.path.exists(condor_lockfile)
    else:
        # In EL7 we no longer have a lockfile
        returncode, _, _ = core.system(['service', 'condor', 'status'])
        return returncode == 0

