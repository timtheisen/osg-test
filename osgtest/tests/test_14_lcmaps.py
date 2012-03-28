import os
import osgtest.library.core as core
import osgtest.library.files as files
import shutil
import unittest

class TestLcMaps(unittest.TestCase):

    # ==================================================================
    def test_01_create_lcmaps_for_glexec(self):
        if not core.rpm_is_installed('glexec'):
            core.skip("glexec not installed, don't need lcmaps for it")
            return
        path='/etc/lcmaps.db'
        
        contents = """
##############################################################################
#
# lcmaps.db
# 
# This is a configuration for lcmaps for testing the ce and glexec. It CAN'T
# be used as-is to test gums.
# 
##############################################################################

glexectracking = "lcmaps_glexec_tracking.mod"
         "-exec /usr/sbin/glexec_monitor"
# Uncomment if your procd is located in a non-standard directory
#         "-procddir /usr"
# Uncomment to write tracking info to glexec_monitor.log in the given dir
#     otherwise the default is to use syslog
#         "-logdir /var/log/glexec"
# Uncomment to change the default logging level for the glexec_monitor
#   Level 0: none, 1: errors, 2: warnings, 3: notices, 4: info, 5: debug
#   The notices level is used for usage tracking; info is commonly useful.
#   Default is lcmaps_debug_level from glexec.conf.
#         "-log-level 4"
# Uncomment to change the syslog facility.  Default is LOG_DAEMON
#	  "-log-facility LOG_DAEMON"
# Uncomment to use local time in the file log (doesn't apply to syslog)
#         "-datetime-local"
# Uncomment to change the minimum tracking group id
#         "-min-gid 65000"
# Uncomment to change the maximum tracking group id
#         "-max-gid 65049"
# Uncomment to not kill processes still running after the main process finishes
#         "-dont-kill-leftovers"

posix_enf = "lcmaps_posix_enf.mod"
            "-maxuid 1 -maxpgid 1 -maxsgid 32"

gridmapfile = "lcmaps_localaccount.mod"
              "-gridmap /etc/grid-security/grid-mapfile"

verifyproxy = "lcmaps_verify_proxy.mod"
          "--allow-limited-proxy"
          " -certdir /etc/grid-security/certificates"

# Mapping policies

#
# Mapping policy: osg_default
# Purpose:        Used for the Globus gatekeeper and the gridftp server
#
osg_default:

gridmapfile -> posix_enf


#
# Mapping policy: glexec
# Purpose:        Used for glexec on the worker nodes.
#
glexec:

verifyproxy -> gridmapfile
gridmapfile -> glexectracking
        """
        files.write(path, contents, backup=True)
