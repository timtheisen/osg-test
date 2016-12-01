import os
import re
import osgtest.library.core as core
import osgtest.library.service as service
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStartGatekeeper(osgunittest.OSGTestCase):

    def test_01_start_gatekeeper(self):
        core.state['globus-gatekeeper.started-service'] = False
        core.state['globus-gatekeeper.running'] = False
        core.skip_ok_unless_installed('globus-gatekeeper')
        core.state['globus-gatekeeper.running'] = service.is_running('globus-gatekeeper')

        if service.is_stopped('globus-gatekeeper'):
            # DEBUG: Set up gatekeeper debugging
            core.config['jobmanager-config'] = '/etc/globus/globus-gram-job-manager.conf'
            conf_path = core.config['jobmanager-config']
            files.append(conf_path, '-log-levels TRACE|DEBUG|FATAL|ERROR|WARN|INFO\n', owner='globus')
            files.append(conf_path, '-log-pattern /var/log/globus/gram_$(LOGNAME)_$(DATE).log\n', backup=False)

            if not os.path.exists('/var/log/globus'):
                os.mkdir('/var/log/globus')
                os.chmod('/var/log/globus', 0777)

            service.check_start('globus-gatekeeper')
            core.state['globus-gatekeeper.started-service'] = True
            core.state['globus-gatekeeper.running'] = True

    def test_02_start_seg(self):
        core.state['globus.started-seg'] = False
        core.skip_ok_unless_installed('globus-scheduler-event-generator-progs')
        # globus-job-run against PBS hangs with the SEG so we disable it and use
        # globus-grid-job-manager-pbs-setup-poll instead
        # https://jira.opensciencegrid.org/browse/SOFTWARE-1929
        self.skip_ok_if(core.el_release() == 5, 'Disable the SEG for EL5')
        self.skip_ok_if(service.is_running('globus-scheduler-event-generator'), 'SEG already running')

        service.check_start('globus-scheduler-event-generator')
        core.state['globus.started-seg'] = True

    def test_03_configure_globus_pbs(self):
        core.config['globus.pbs-config'] = '/etc/globus/globus-pbs.conf'
        core.state['globus.pbs_configured'] = False
        core.skip_ok_unless_installed('globus-gram-job-manager-pbs')
        config_file = file(core.config['globus.pbs-config']).read()
        server_name = core.get_hostname()
        re_obj = re.compile('^pbs_default=.*$', re.MULTILINE)
        if 'pbs_default' in config_file:
            config_file = re_obj.sub("pbs_default=\"%s\"" % server_name, 
                                     config_file)
        else:
            config_file += "pbs_default=\"%s\"" % server_name
        files.write(core.config['globus.pbs-config'], config_file, owner='pbs')
        core.state['globus.pbs_configured'] = True
