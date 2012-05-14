import os
import osgtest.library.core as core
import osgtest.library.files as files
import unittest

class TestStartGatekeeper(unittest.TestCase):

    def test_01_start_gatekeeper(self):
        core.config['globus.gk-lockfile'] = '/var/lock/subsys/globus-gatekeeper'
        core.state['globus.started-gk'] = False

        if not core.rpm_is_installed('globus-gatekeeper'):
            core.skip('not installed')
            return
        if os.path.exists(core.config['globus.gk-lockfile']):
            core.skip('apparently running')
            return

        # DEBUG: Set up gatekeeper debugging
        core.config['jobmanager-config'] = '/etc/globus/globus-gram-job-manager.conf'
        files.append_line(core.config['jobmanager-config'], '-log-levels TRACE|DEBUG|FATAL|ERROR|WARN|INFO\n', if_not_present=True)
        files.append_line(core.config['jobmanager-config'], '-log-pattern /var/log/globus/gram_$(LOGNAME)_$(DATE).log\n', if_not_present=True)

        if not os.path.exists('/var/log/globus'):
            os.mkdir('/var/log/globus')
            os.chmod('/var/log/globus', 0777)

        command = ('service', 'globus-gatekeeper', 'start')
        stdout, _, fail = core.check_system(command, 'Start Globus gatekeeper')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(os.path.exists(core.config['globus.gk-lockfile']),
                     'Globus gatekeeper run lock file missing')
        core.state['globus.started-gk'] = True

    def test_02_start_seg(self):
        core.state['globus.started-seg'] = False
        core.config['globus.seg-lockfile'] = '/var/lock/subsys/globus-scheduler-event-generator'

        if not core.rpm_is_installed('globus-scheduler-event-generator-progs'):
            core.skip('Globus SEG not installed')
            return
        if os.path.exists(core.config['globus.seg-lockfile']):
            core.skip('SEG apparently running')
            return
        command = ('service', 'globus-scheduler-event-generator', 'start')
        stdout, _, fail = core.check_system(command, 'Start Globus SEG')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(os.path.exists(core.config['globus.seg-lockfile']),
                     'Globus SEG run lock file missing')
        core.state['globus.started-seg'] = True
