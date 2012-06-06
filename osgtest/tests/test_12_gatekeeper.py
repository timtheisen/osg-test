import os, re
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
        conf_path = core.config['jobmanager-config']
        files.append(conf_path, '-log-levels TRACE|DEBUG|FATAL|ERROR|WARN|INFO\n', owner='globus')
        files.append(conf_path, '-log-pattern /var/log/globus/gram_$(LOGNAME)_$(DATE).log\n', backup=False)

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

    def test_03_configure_globus_pbs(self):
        core.config['globus.pbs-config'] = '/etc/globus/globus-pbs.conf'
        core.state['globus.pbs_configured'] = False
        if not core.rpm_is_installed('globus-gram-job-manager-pbs'):
            return
        config_file = file(core.config['globus.pbs-config']).read()
        server_name = core.get_hostname()
        re_obj = re.compile('^pbs_default=.*$', re.MULTILINE)
        if 'pbs_default' in config_file:
            config_file = re_obj.sub("pbs_default=\"%s\"" % server_name, 
                                     config_file)
        else:
            config_file += "pbs_default=\"%s\"" % server_name
        files.write(core.config['globus.pbs-config'], config_file, 'pbs')
        core.state['globus.pbs_configured'] = True
