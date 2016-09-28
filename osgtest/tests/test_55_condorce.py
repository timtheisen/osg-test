#pylint: disable=C0301
#pylint: disable=R0904

import os
import re

import osgtest.library.condor as condor
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestCondorCE(osgunittest.OSGTestCase):
    def general_requirements(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client')
        self.skip_bad_unless(core.state['condor-ce.started-service'], 'ce not running')

    def test_01_status(self):
        self.general_requirements()

        command = ('condor_ce_status', '-any')
        core.check_system(command, 'ce status', user=True)

    def test_02_queue(self):
        self.general_requirements()

        command = ('condor_ce_q', '-verbose')
        core.check_system(command, 'ce queue', user=True)

    def test_03_ping(self):
        self.general_requirements()

        command = ('condor_ce_ping', 'WRITE', '-verbose')
        stdout, _, _ = core.check_system(command, 'ping using GSI and gridmap', user=True)
        self.assert_(re.search(r'Authorized:\s*TRUE', stdout), 'could not authorize with GSI')

    def test_04_trace(self):
        self.general_requirements()
        self.skip_bad_unless(core.state['condor-ce.schedd-ready'], 'CE schedd not ready to accept jobs')

        cwd = os.getcwd()
        os.chdir('/tmp')

        command = ('condor_ce_trace', '--debug', core.get_hostname())
        core.check_system(command, 'ce trace', user=True)

        os.chdir(cwd)

    def test_05_pbs_trace(self):
        self.general_requirements()
        self.skip_bad_unless(core.state['condor-ce.schedd-ready'], 'CE schedd not ready to accept jobs')
        core.skip_ok_unless_installed('torque-mom', 'torque-server', 'torque-scheduler', 'torque-client', 'munge')
        self.skip_ok_unless(core.state['torque.pbs-server-running'])

        cwd = os.getcwd()
        os.chdir('/tmp')

        command = ('condor_ce_trace', '-a osgTestPBS = True', '--debug', core.get_hostname())
        core.check_system(command, 'ce trace against pbs', user=True)

        os.chdir(cwd)

    def test_06_use_gums_auth(self):
        core.state['condor-ce.gums-auth'] = False
        self.general_requirements()
        core.skip_ok_unless_installed('gums-service')

        # Setting up GUMS auth using the instructions here:
        # twiki.grid.iu.edu/bin/view/Documentation/Release3/InstallComputeElement#8_1_Using_GUMS_for_Authorization
        hostname = core.get_hostname()

        lcmaps_contents = '''gumsclient = "lcmaps_gums_client.mod"
             "-resourcetype ce"
             "-actiontype execute-now"
             "-capath /etc/grid-security/certificates"
             "-cert   /etc/grid-security/hostcert.pem"
             "-key    /etc/grid-security/hostkey.pem"
             "--cert-owner root"
# Change this URL to your GUMS server
             "--endpoint https://%s:8443/gums/services/GUMSXACMLAuthorizationServicePort"

verifyproxy = "lcmaps_verify_proxy.mod"
          "--allow-limited-proxy"
          " -certdir /etc/grid-security/certificates"

# lcmaps policies require at least two modules, so these are here to
#   fill in if only one module is needed.  "good | bad" has no effect.
good        = "lcmaps_dummy_good.mod"
bad         = "lcmaps_dummy_bad.mod"

authorize_only:
## Policy 1: GUMS but not SAZ (most common, default)
gumsclient -> good | bad
''' % hostname

        gums_properties_contents = '''gums.location=https://%s:8443/gums/services/GUMSAdmin
gums.authz=https://%s:8443/gums/services/GUMSXACMLAuthorizationServicePort
''' % (hostname, hostname)

        core.config['condor-ce.gums-properties'] = '/etc/gums/gums-client.properties'
        core.config['condor-ce.gsi-authz'] = '/etc/grid-security/gsi-authz.conf'

        files.write(core.config['condor-ce.lcmapsdb'], lcmaps_contents, owner='condor-ce.gums')
        files.write(core.config['condor-ce.gums-properties'], gums_properties_contents, owner='condor-ce')
        files.replace(core.config['condor-ce.gsi-authz'],
                      '# globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout',
                      'globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout',
                      owner='condor-ce')

        service.stop('condor-ce')
        service.start('condor-ce')
        core.state['condor-ce.gums-auth'] = True

    def test_07_ping_with_gums(self):
        self.general_requirements()
        core.skip_ok_unless_installed('gums-service')
        self.skip_bad_unless(core.state['condor-ce.gums-auth'], 'CE not using GUMS auth')

        # Wait for the schedd to come back up
        try:
            stat = os.stat(core.config['condor-ce.collectorlog'])
        except OSError:
            stat = None
        self.failUnless(condor.wait_for_daemon(core.config['condor-ce.collectorlog'], stat, 'Schedd', 300.0),
                        'Schedd failed to restart within the 1 min window')
        command = ('condor_ce_ping', 'WRITE', '-verbose')
        stdout, _, _ = core.check_system(command, 'ping using GSI and gridmap', user=True)
        self.assert_(re.search(r'Authorized:\s*TRUE', stdout), 'could not authorize with GSI')
