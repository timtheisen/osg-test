#pylint: disable=C0301
#pylint: disable=R0201
#pylint: disable=R0904

import os
import rpm
import shutil
import tempfile

import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest

class TestRunJobs(osgunittest.OSGTestCase):

    def verify_job_environment(self, output):
        expected_env = {'JOB_ENV': 'vdt',
                        'LOCAL_JOB_ENV': 'osg'}
        env = core.parse_env_output(output)
        self.assertSubsetOf(expected_env, env, 'Could not verify OSG job environment')

    def run_job_in_tmp_dir(self, command, message, verify_environment=True):
        tmp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(tmp_dir)
        os.chmod(tmp_dir, 0777)

        stdout = core.check_system(command, message, user=True)[0]

        if verify_environment:
            self.verify_job_environment(stdout)

        os.chdir(old_cwd)
        shutil.rmtree(tmp_dir)

    def contact_string(self, jobmanager):
        return core.get_hostname() + '/jobmanager-' + jobmanager

    def test_01_globus_run_fork(self):
        core.skip_ok_unless_installed(
            'globus-gatekeeper', 'globus-gram-client-tools',
            'globus-proxy-utils', 'globus-gram-job-manager',
            'globus-gram-job-manager-fork-setup-poll')
        self.skip_bad_unless(core.state['globus.started-gk'], 'gatekeeper not started')
        self.skip_bad_unless(core.state['jobs.env-set'], 'job environment not set')

        command = ('globus-job-run', self.contact_string('fork'), '/bin/env')
        stdout = core.check_system(command, 'globus-job-run a fork job', user=True)[0]
        self.verify_job_environment(stdout)

    def test_02_globus_run_condor(self):
        core.skip_ok_unless_installed('globus-gram-job-manager-condor', 'globus-gram-client-tools', 'globus-proxy-utils')
        self.skip_bad_unless(core.state['globus.started-gk'], 'gatekeeper not started')
        self.skip_bad_unless(core.state['jobs.env-set'], 'job environment not set')
        self.skip_bad_unless(core.state['condor.running-service'], message='Condor service not running')

        command = ('globus-job-run', self.contact_string('condor'), '/bin/env')
        stdout = core.check_system(command, 'globus-job-run a Condor job', user=True)[0]
        self.verify_job_environment(stdout)

    def test_03_globus_run_pbs(self):
        core.skip_ok_unless_installed('globus-gram-job-manager-pbs', 'globus-gram-client-tools', 'globus-proxy-utils',
                                      'torque-mom', 'torque-server', 'torque-scheduler')
        self.skip_bad_unless(core.state['globus.started-gk'], 'gatekeeper not started')
        self.skip_bad_unless(core.state['jobs.env-set'], 'job environment not set')
        if (not core.state['torque.pbs-configured'] or
            not core.state['torque.pbs-mom-running'] or
            not core.state['torque.pbs-server-running'] or
            not core.state['globus.pbs_configured']):
            self.skip_bad('pbs not running or configured')

        # Verify job environments set in /var/lib/osg/osg-*job-environment.conf
        command = ('globus-job-run', self.contact_string('pbs'), '/bin/env')
        stdout = core.check_system(command, 'globus-job-run a PBS job', user=True)[0]
        self.verify_job_environment(stdout)

    def test_04_condor_run_pbs(self):
        core.skip_ok_unless_installed('condor', 'blahp', 'torque-mom', 'torque-server', 'torque-scheduler',
                                      'globus-gatekeeper')
        self.skip_bad_unless(core.state['globus.started-gk'], 'gatekeeper not started')
        self.skip_bad_unless(core.state['jobs.env-set'], 'job environment not set')
        self.skip_bad_unless(core.state['condor.running-service'], 'condor not running')
        self.skip_bad_unless(core.state['torque.pbs-mom-running'] and core.state['torque.pbs-server-running'],
                             'pbs not running')

        command = ('condor_run', '-u', 'grid', '-a', 'grid_resource=pbs', '-a', 'periodic_remove=JobStatus==5',
                   '/bin/env')

        # Figure out whether the installed BLAHP package is the same as or later
        # than "blahp-1.18.11.bosco-4.osg*" (in the RPM sense), because it's the
        # first build in which the job environments are correctly passed to PBS.
        # The release following "osg" does not matter and it is easier to ignore
        # the OS major version.  This code may be a useful starting point for a
        # more general library function.
        blahp_envra = core.get_package_envra('blahp')
        blahp_pbs_has_env_vars = (rpm.labelCompare(['blahp', '1.18.11.bosco', '4.osg'], blahp_envra[1:4]) <= 0)

        self.run_job_in_tmp_dir(command, 'condor_run a Condor job', verify_environment=blahp_pbs_has_env_vars)

    def test_05_condor_ce_run_condor(self):
        core.skip_ok_unless_installed('htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor', 'condor')

        self.skip_bad_unless('condor-ce.started', 'ce not running')
        self.skip_bad_unless(core.state['jobs.env-set'], 'job environment not set')

        command = ('condor_ce_run', '-r', '%s:9619' % core.get_hostname(), '/bin/env')
        self.run_job_in_tmp_dir(command, 'condor_ce_run a Condor job')
