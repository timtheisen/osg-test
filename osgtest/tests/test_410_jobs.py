#pylint: disable=C0301
#pylint: disable=R0201
#pylint: disable=R0904

import os
import shutil
import tempfile

import osgtest.library.core as core
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestRunJobs(osgunittest.OSGTestCase):

    def tearDown(self):
        env_vars = ('_condor_SCITOKENS_FILE',
                    'BEARER_TOKEN_FILE')

        [ os.environ.pop(env_var, None) for env_var in env_vars ]

    def verify_job_environment(self, output):
        expected_env = {'JOB_ENV': 'vdt',
                        'LOCAL_JOB_ENV': 'osg'}
        env = core.parse_env_output(output)
        self.assertSubsetOf(expected_env, env, 'Could not verify OSG job environment')

    def run_job_in_tmp_dir(self, command, message, verify_environment=True):
        tmp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(tmp_dir)
        os.chmod(tmp_dir, 0o777)

        try:
            stdout = core.check_system(command, message, user=True, timeout=600)[0]
        except osgunittest.TimeoutException:
            self.fail("Job failed to complete in 10 minute window")

        if verify_environment:
            self.verify_job_environment(stdout)

        os.chdir(old_cwd)
        shutil.rmtree(tmp_dir)

    def test_01_condor_run_pbs(self):
        core.skip_ok_unless_installed('condor')
        core.skip_ok_unless_installed('torque-mom', 'torque-server', 'torque-scheduler', by_dependency=True)
        self.skip_bad_unless(core.state['jobs.env-set'], 'job environment not set')
        self.skip_bad_unless(service.is_running('condor'), 'condor not running')
        self.skip_bad_unless(service.is_running('pbs_server'), 'pbs not running')

        command = ('condor_run', '-u', 'grid', '-a', 'grid_resource=pbs', '-a', 'periodic_remove=JobStatus==5',
                   '/bin/env')

        self.run_job_in_tmp_dir(command, 'condor_run a Condor job')

    def test_02_condor_ce_run_condor(self):
        core.skip_ok_unless_installed('htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor', 'condor')

        self.skip_bad_unless(service.is_running('condor-ce'), 'ce not running')
        self.skip_bad_unless(service.is_running('condor'), 'condor not running')
        self.skip_bad_unless(core.state['jobs.env-set'], 'job environment not set')
        token_file = core.config['token.condor_write']
        self.skip_bad_unless(core.state['proxy.valid'] or os.path.exists(token_file),
                             'requires a scitoken or a proxy')

        command = ['condor_ce_run', '--debug', '-r', '%s:9619' % core.get_hostname(), '/bin/env']

        if os.path.exists(token_file):
            # FIXME: After HTCONDOR-636 is released (targeted for HTCondor-CE 5.1.2),
            # we can stop setting _condor_SCITOKENS_FILE
            for token_var in ('_condor_SCITOKENS_FILE',
                              'BEARER_TOKEN_FILE'):
                os.environ[token_var] = token_file
        else:
            core.log_message('condor WRITE token not found; skipping SCITOKENS auth')

        with core.no_x509(core.options.username):
            self.run_job_in_tmp_dir(command, 'condor_ce_run a Condor job')
