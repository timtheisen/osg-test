import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import unittest
import tempfile
import os
import shutil

class TestGlobusJobRun(osgunittest.OSGTestCase):

    def assertJobEnv(self, output):
        expected_env = {'JOB_ENV': 'vdt',
                        'LOCAL_JOB_ENV': 'osg'}
        env = core.parse_env_output(output)        
        self.assertSubsetOf(expected_env, env, 'Could not verify OSG job environment')

    def contact_string(self, jobmanager):
        return core.get_hostname() + '/jobmanager-' + jobmanager

    def test_01_fork_job(self):
        core.skip_ok_unless_installed(
            'globus-gatekeeper', 'globus-gram-client-tools',
            'globus-proxy-utils', 'globus-gram-job-manager',
            'globus-gram-job-manager-fork-setup-poll')
        self.skip_bad_unless(core.state['globus.started-gk'], 'gatekeeper not started')
        
        command = ('globus-job-run', self.contact_string('fork'), '/bin/echo', 'hello')
        stdout = core.check_system(command, 'globus-job-run on fork job', user=True)[0]
        self.assertEqual(stdout, 'hello\n', 'Incorrect output from globus-job-run on fork job')

    def test_02_condor_job(self):
        core.skip_ok_unless_installed('globus-gram-job-manager-condor', 'globus-gram-client-tools', 'globus-proxy-utils')
        self.skip_bad_unless(core.state['globus.started-gk'], 'gatekeeper not started')
        self.skip_bad_unless(core.state['condor.running-service'], message='Condor service not running')

        command = ('globus-job-run', self.contact_string('condor'), '/bin/env')
        stdout = core.check_system(command, 'globus-job-run on Condor job', user=True)[0]
        self.assertJobEnv(stdout)

    def test_03_pbs_job(self):
        core.skip_ok_unless_installed('globus-gram-job-manager-pbs', 'globus-gram-client-tools', 'globus-proxy-utils',
                                      'torque-mom', 'torque-server', 'torque-scheduler')
        self.skip_bad_unless(core.state['globus.started-gk'], 'gatekeeper not started')
        if (not core.state['torque.pbs-configured'] or
            not core.state['torque.pbs-mom-running'] or
            not core.state['torque.pbs-server-running'] or
            not core.state['globus.pbs_configured']):
            self.skip_bad('pbs not running or configured')

        # Verify job environments set in /var/lib/osg/osg-*job-environment.conf
        command = ('globus-job-run', self.contact_string('pbs'), '/bin/env')
        stdout = core.check_system(command, 'globus-job-run on PBS job', user=True)[0]
        self.assertJobEnv(stdout)

    def test_04_blahp_pbs_job(self):
        core.skip_ok_unless_installed('condor', 'blahp','torque-mom', 'torque-server', 'torque-scheduler', 'globus-gatekeeper')
        self.skip_bad_unless(core.state['globus.started-gk'], 'gatekeeper not started')
        self.skip_bad_unless(core.state['condor.running-service'], 'condor not running')
        self.skip_bad_unless(core.state['torque.pbs-mom-running'] and core.state['torque.pbs-server-running'],
                             'pbs not running')
        
        tmp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(tmp_dir)
        os.chmod(tmp_dir, 0777)

        command = ('condor_run', '-u', 'grid', '-a', 'grid_resource=pbs', '-a', 'periodic_remove=JobStatus==5', '/bin/env')
        stdout = core.check_system(command, 'condor_run on pbs job', user=True)[0]

        os.chdir(old_cwd)
        shutil.rmtree(tmp_dir)

        self.assertJobEnv(stdout)

