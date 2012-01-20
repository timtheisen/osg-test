import os
import osgtest.library.core as core
import time
import unittest

class TestRunningJobs(unittest.TestCase):

    # "Constants"
    __lockfile_gatekeeper = '/var/lock/subsys/globus-gatekeeper'
    __lockfile_condor = '/var/lock/subsys/condor_master'

    # Class attributes
    __started_gatekeeper = False
    __started_condor = False

    def test_01_grid_proxy_init(self):
        if not core.rpm_is_installed('globus-proxy-utils'):
            core.skip()
            return
        command = ('grid-proxy-init', '-debug')
        password = core.options.password + '\n'
        status, stdout, stderr = core.syspipe(command, True, password)
        fail = core.diagnose('Run grid-proxy-init', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    def test_10_start_gatekeeper(self):
        TestRunningJobs.__started_gatekeeper = False
        if not core.rpm_is_installed('globus-gatekeeper'):
            core.skip('not installed')
            return
        if os.path.exists(TestRunningJobs.__lockfile_gatekeeper):
            core.skip('apparently running')
            return

        # DEBUG: Set up gatekeeper debugging
        jobmanager_config = open('/etc/globus/globus-gram-job-manager.conf', 'a')
        jobmanager_config.write('-log-levels TRACE|DEBUG|FATAL|ERROR|WARN|INFO\n')
        jobmanager_config.write('-log-pattern /var/log/globus/gram_$(LOGNAME)_$(DATE).log\n')
        jobmanager_config.close()
        if not os.path.exists('/var/log/globus'):
            os.mkdir('/var/log/globus')
            os.chmod('/var/log/globus', 0777)

        command = ('service', 'globus-gatekeeper', 'start')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Start Globus gatekeeper', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(stdout.find('FAILED') == -1,
                     "Starting the Globus gatekeeper reported 'FAILED'")
        self.assert_(os.path.exists(TestRunningJobs.__lockfile_gatekeeper),
                     'Globus gatekeeper run lock file missing')
        TestRunningJobs.__started_gatekeeper = True

    def test_12_start_condor(self):
        TestRunningJobs.__started_condor = False
        if not core.rpm_is_installed('condor'):
            core.skip('not installed')
            return
        if os.path.exists(TestRunningJobs.__lockfile_condor):
            core.skip('apparently running')
            return

        command = ('service', 'condor', 'start')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Start Condor', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(stdout.find('error') == -1,
                     "Starting Condor reported 'error'")
        self.assert_(os.path.exists(TestRunningJobs.__lockfile_condor),
                     'Condor run lock file missing')
        TestRunningJobs.__started_condor = True

    def test_20_fork_job(self):
        if core.missing_rpm('globus-gatekeeper', 'globus-gram-client-tools',
                            'globus-proxy-utils', 'globus-gram-job-manager',
                            'globus-gram-job-manager-fork-setup-poll'):
            return

        command = ('globus-job-run', 'localhost/jobmanager-fork', '/bin/echo',
                   'hello')
        status, stdout, stderr = core.syspipe(command, True)
        fail = core.diagnose('Failed globus-job-run on fork job',
                             status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout, 'hello\n',
                         'Incorrect output from globus-job-run with fork job')

    def test_30_condor_job(self):
        if core.missing_rpm('globus-gram-job-manager-condor',
                            'globus-gram-client-tools', 'globus-proxy-utils'):
            return

        command = ('globus-job-run', 'localhost/jobmanager-condor', '/bin/echo',
                   'hello')
        status, stdout, stderr = core.syspipe(command, True)
        fail = core.diagnose('Failed globus-job-run on Condor job',
                             status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout, 'hello\n',
                         'Incorrect output from globus-job-run with Condor job')

    def test_50_sleep(self):
        if TestRunningJobs.__started_condor:
            time.sleep(5)

    def test_94_stop_condor(self):
        if not core.rpm_is_installed('condor'):
            core.skip('not installed')
            return
        if TestRunningJobs.__started_condor == False:
            core.skip('did not start server')
            return

        command = ('service', 'condor', 'stop')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Stop Condor', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(stdout.find('error') == -1,
                     "Stopping Condor reported 'error'")
        self.assert_(not os.path.exists(TestRunningJobs.__lockfile_condor),
                     'Condor run lock file still present')

    def test_95_stop_gatekeeper(self):
        if not core.rpm_is_installed('globus-gatekeeper'):
            core.skip('not installed')
            return
        if TestRunningJobs.__started_gatekeeper == False:
            core.skip('did not start server')
            return

        command = ('service', 'globus-gatekeeper', 'stop')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Stop Globus gatekeeper', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(stdout.find('FAILED') == -1,
                     "Stopping the Globus gatekeeper reported 'FAILED'")
        self.assert_(not
                     os.path.exists(TestRunningJobs.__lockfile_gatekeeper),
                     'Globus gatekeeper run lock file still present')
