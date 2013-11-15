import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import unittest
import tempfile
import os
import shutil

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

    def test_04_blahp_pbs_job(self):
        if core.missing_rpm('condor', 'blahp',
                            'torque-mom', 'torque-server',
                            'torque-scheduler'):
            return

        if (not core.state['torque.pbs-mom-running'] or
            not core.state['torque.pbs-server-running']):
          core.skip('pbs not running')
          return

        if (not core.state['condor.running-service']):
          core.skip('condor not running')
          return
        
        tmp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(tmp_dir)
        os.chmod(tmp_dir, 0777)
        
        command = "/usr/bin/condor_run -u grid -a grid_resource=pbs -a periodic_remove=JobStatus==5 /bin/echo hello".split()
        stdout = core.check_system(command, 'condor_run on pbs job', user=True)[0]

        os.chdir(old_cwd)
        shutil.rmtree(tmp_dir)
        
        self.assertEqual(stdout, 'hello\n', 'Incorrect output from condor_run on pbs job')



