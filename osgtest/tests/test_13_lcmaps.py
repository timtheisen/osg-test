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
# Please note that the below is a non-standard lcmaps.db meant for testing specifically glexec. Other applications will
# require adjustments

path = lcmaps

gumsclient = "lcmaps_gums_client.mod"
             "-resourcetype ce"
             "-actiontype execute-now"
             "-capath /etc/grid-security/certificates"
             "-cert   /etc/grid-security/hostcert.pem"
             "-key    /etc/grid-security/hostkey.pem"
             "--cert-owner root"
# Change this URL to your GUMS server
             "--endpoint https://yourgums.yourdomain:8443/gums/services/GUMSXACMLAuthorizationServicePort"
# Uncomment this to set a different expected host certificate name for server
#            "--override-expected-hostname overridegumsname.yourdomain"

sazclient = "lcmaps_saz_client.mod"
            "-resourcetype ce"
            "-actiontype execute-now"
            "-capath /etc/grid-security/certificates"
            "-cert   /etc/grid-security/hostcert.pem"
            "-key    /etc/grid-security/hostkey.pem"
            "--cert-owner root"
            "-authorization-only"
# Change this URL to your SAZ server if you have one
            "--endpoint https://yoursaz.yourdomain:8443/saz/services/SAZXACMLAuthorizationServicePort"
# Uncomment this to set a different expected host certificate name for server
#            "--override-expected-hostname overridesazname.yourdomain"

# Uncomment if your procd is located in a non-standard directory
#           "-procddir /usr"
# Uncomment to write tracking info to glexec_monitor.log in the given dir
#     otherwise the default is to use syslog
#         "-logdir /var/log/glexec"
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

# These two lines were originally comemnted out, but these are exactly what we need to glexec
glexectracking = "lcmaps_glexec_tracking.mod"
               "-exec /usr/sbin/glexec_monitor"


#-----------------------------------------------------------------------------
#
# Mapping policies
#
# Each of these define how lcmaps is used in different scenarios.
# The defaults are generally good.
# We've left the various glexec policies commented out--you need to
# choose one of the three policies. Most sites will use the first
# policy (verify proxy, gums client, glexectracking). Do not uncomment
# the glexec policies if you are not using glexec!
#
# For the globus_gridftp_mapping and the osg_default mapping, we've
# shown how to add saz, if you are using it at your site. Uncomment
# that line if appropriate.
#
#-----------------------------------------------------------------------------

#
# Mapping policy: globus_gridftp_mapping
# Purpose:        Used for gridftp
#
globus_gridftp_mapping:
#Uncomment this one line to add SAZ
#sazclient -> gumsclient
gumsclient -> posix_enf

#
# Mapping policy: osg_default
# Purpose:        Used for the Globus gatekeeper
#
osg_default:
verifyproxy -> gumsclient
#Uncomment the next two lines and comment the previous line to add SAZ
#verifyproxy -> sazclient
#sazclient -> gumsclient

#
# Mapping policy: glexec
# Purpose:        Used for glexec on the worker nodes.
#
glexec:

## Pick an appropriate policy from the ones below. Make sure that only
## one policy is uncommented--the other policies should be commented
## out. For example, if you want policy #1 (the most common), remove
## the hash mark two lines: just before "verifyproxy" and just before
## "gumsclient".

## Policy 1: GUMS but not SAZ (most common)
#verifyproxy -> gumsclient
#gumsclient -> glexectracking

## Policy 2: GUMS & SAZ
#verifyproxy -> sazclient
#sazclient -> gumsclient
#gumsclient -> glexectracking

## Policy 3: grid-mapfile
verifyproxy -> gridmapfile
gridmapfile -> glexectracking

        """
        files.write(path, contents, backup=False)
