import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import unittest

class TestGlobusJobRun(osgunittest.OSGTestCase):

    def contact_string(self, jobmanager):
        return core.get_hostname() + '/jobmanager-' + jobmanager

    def test_01_fork_job(self):
        core.skip_ok_unless_installed(
            'globus-gatekeeper', 'globus-gram-client-tools',
            'globus-proxy-utils', 'globus-gram-job-manager',
            'globus-gram-job-manager-fork-setup-poll')
        
        command = ('globus-job-run', self.contact_string('fork'), '/bin/echo', 'hello')
        stdout = core.check_system(command, 'globus-job-run on fork job', user=True)[0]
        self.assertEqual(stdout, 'hello\n',
                         'Incorrect output from globus-job-run on fork job')

    def test_02_condor_job(self):
        core.skip_ok_unless_installed('globus-gram-job-manager-condor', 'globus-gram-client-tools', 'globus-proxy-utils')
        
        self.skip_bad_unless(core.state['condor.running-service'], message='Condor service not running')

        command = ('globus-job-run', self.contact_string('condor'), '/bin/echo', 'hello')
        stdout = core.check_system(command, 'globus-job-run on Condor job', user=True)[0]
        self.assertEqual(stdout, 'hello\n',
                         'Incorrect output from globus-job-run on Condor job')

    def test_03_pbs_job(self):
        core.skip_ok_unless_installed('globus-gram-job-manager-pbs', 'globus-gram-client-tools', 'globus-proxy-utils')
        # ^ should also check for torque rpms?

        if (not core.state['torque.pbs-configured'] or
            not core.state['torque.pbs-mom-running'] or
            not core.state['torque.pbs-server-running'] or
            not core.state['globus.pbs_configured']):
            
            self.skip_bad('pbs not running or configured')

        command = ('globus-job-run', self.contact_string('pbs'), '/bin/echo', 'hello')
        stdout = core.check_system(command, 'globus-job-run on PBS job', user=True)[0]
        self.assertEqual(stdout, 'hello\n',
                         'Incorrect output from globus-job-run on PBS job')
