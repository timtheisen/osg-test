import os
import osgtest.library.core as core
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
        jobmanager_config = open('/etc/globus/globus-gram-job-manager.conf', 'a')
        jobmanager_config.write('-log-levels TRACE|DEBUG|FATAL|ERROR|WARN|INFO\n')
        jobmanager_config.write('-log-pattern /var/log/globus/gram_$(LOGNAME)_$(DATE).log\n')
        jobmanager_config.close()
        if not os.path.exists('/var/log/globus'):
            os.mkdir('/var/log/globus')
            os.chmod('/var/log/globus', 0777)

        command = ('service', 'globus-gatekeeper', 'start')
        stdout, _, fail = core.check_system(command, 'Start Globus gatekeeper')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(os.path.exists(core.config['globus.gk-lockfile']),
                     'Globus gatekeeper run lock file missing')
        core.state['globus.started-gk'] = True
