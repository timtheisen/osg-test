import os
import osgtest
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
        if not osgtest.rpm_is_installed('globus-proxy-utils'):
            osgtest.skip()
            return
        command = ['grid-proxy-init', '-debug']
        password = osgtest.options.password + '\n'
        (status, stdout, stderr) = osgtest.syspipe(command, True, password)
        fail = osgtest.diagnose('Run grid-proxy-init', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    def test_10_start_gatekeeper(self):
        TestRunningJobs.__started_gatekeeper = False
        if not osgtest.rpm_is_installed('globus-gatekeeper'):
            osgtest.skip('not installed')
            return
        if os.path.exists(TestRunningJobs.__lockfile_gatekeeper):
            osgtest.skip('apparently running')
            return

        command = ['service', 'globus-gatekeeper', 'start']
        (status, stdout, stderr) = osgtest.syspipe(command)
        self.assertEqual(status, 0, "Starting the Globus gatekeeper failed "
                         "with exit status %d" % status)
        self.assert_(stdout.find('FAILED') == -1,
                     "Starting the Globus gatekeeper reported 'FAILED'")
        self.assert_(os.path.exists(TestRunningJobs.__lockfile_gatekeeper),
                     'Globus gatekeeper run lock file missing')
        TestRunningJobs.__started_gatekeeper = True

    def test_12_start_condor(self):
        TestRunningJobs.__started_condor = False
        if not osgtest.rpm_is_installed('condor'):
            osgtest.skip('not installed')
            return
        if os.path.exists(TestRunningJobs.__lockfile_condor):
            osgtest.skip('apparently running')
            return

        command = ['service', 'condor', 'start']
        (status, stdout, stderr) = osgtest.syspipe(command)
        self.assertEqual(status, 0,
                         "Starting Condor failed with exit status %d" % status)
        self.assert_(stdout.find('error') == -1,
                     "Starting Condor reported 'error'")
        self.assert_(os.path.exists(TestRunningJobs.__lockfile_condor),
                     'Condor run lock file missing')
        TestRunningJobs.__started_condor = True

    def test_20_fork_job(self):
        if osgtest.missing_rpm(['globus-gatekeeper', 'globus-gram-client-tools',
                                'globus-proxy-utils', 'globus-gram-job-manager',
                                'globus-gram-job-manager-fork-setup-poll']):
            return

        command = ['globus-job-run', 'localhost/jobmanager-fork',
                   '/bin/echo', 'hello']
        (status, stdout, stderr) = osgtest.syspipe(command, True)
        fail = osgtest.diagnose('Failed globus-job-run on fork job',
                                status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout, 'hello\n',
                         'Incorrect output from globus-job-run with fork job')

    def test_30_condor_job(self):
        if osgtest.missing_rpm(['globus-gram-job-manager-condor',
                                'globus-gram-client-tools',
                                'globus-proxy-utils']):
            return

        command = ['globus-job-run', 'localhost/jobmanager-condor',
                   '/bin/echo', 'hello']
        (status, stdout, stderr) = osgtest.syspipe(command, True)
        fail = osgtest.diagnose('Failed globus-job-run on Condor job',
                                status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout, 'hello\n',
                         'Incorrect output from globus-job-run with Condor job')

    def test_50_sleep(self):
        time.sleep(5)

    def test_94_stop_condor(self):
        if not osgtest.rpm_is_installed('condor'):
            osgtest.skip('not installed')
            return
        if TestRunningJobs.__started_condor == False:
            osgtest.skip('did not start server')
            return

        command = ['service', 'condor', 'stop']
        (status, stdout, stderr) = osgtest.syspipe(command)
        self.assertEqual(status, 0,
                         'Stopping Condor failed with exit status %d\n%s\n%s' \
                         % (status, stdout, stderr))
        self.assert_(stdout.find('error') == -1,
                     "Stopping Condor reported 'error'")
        self.assert_(not os.path.exists(TestRunningJobs.__lockfile_condor),
                     'Condor run lock file still present')

    def test_95_stop_gatekeeper(self):
        if not osgtest.rpm_is_installed('globus-gatekeeper'):
            osgtest.skip('not installed')
            return
        if TestRunningJobs.__started_gatekeeper == False:
            osgtest.skip('did not start server')
            return

        command = ['service', 'globus-gatekeeper', 'stop']
        (status, stdout, stderr) = osgtest.syspipe(command)
        self.assertEqual(status, 0, "Stopping the Globus gatekeeper failed "
                         "with exit status %d" % status)
        self.assert_(stdout.find('FAILED') == -1,
                     "Stopping the Globus gatekeeper reported 'FAILED'")
        self.assert_(not
                     os.path.exists(TestRunningJobs.__lockfile_gatekeeper),
                     'Globus gatekeeper run lock file still present')
