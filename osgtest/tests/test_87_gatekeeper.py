import os
import osgtest.library.core as core
import osgtest.library.files as files
import unittest

class TestStopGatekeeper(unittest.TestCase):

    def test_01_stop_gatekeeper(self):
        if not core.rpm_is_installed('globus-gatekeeper'):
            core.skip('not installed')
            return
        if core.state['globus.started-gk'] == False:
            core.skip('did not start server')
            return

        files.restore(core.config['jobmanager-config'], 'globus')

        command = ('service', 'globus-gatekeeper', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop Globus gatekeeper')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(not os.path.exists(core.config['globus.gk-lockfile']),
                     'Globus gatekeeper run lock file still present')

    def test_02_stop_seg(self):
        if not core.rpm_is_installed('globus-scheduler-event-generator-progs'):
            core.skip('Globus SEG not installed')
            return
        if core.state['globus.started-seg'] == False:
            core.skip('SEG apparently running')
            return
        command = ('service', 'globus-scheduler-event-generator', 'stop')
        stdout, _, fail = core.check_system(command, 'Start Globus SEG')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(not os.path.exists(core.config['globus.seg-lockfile']),
                     'Globus SEG run lock file still present')
        core.state['globus.started-seg'] = False

    def test_03_configure_globus_pbs(self):
        if not core.state['globus.pbs_configured']:
            core.skip('Globus pbs configuration not altered')
        if not core.rpm_is_installed('globus-gram-job-manager-pbs'):
            return
        files.restore(core.config['globus.pbs-config'], 'pbs')
