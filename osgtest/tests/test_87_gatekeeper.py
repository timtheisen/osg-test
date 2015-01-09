import os
import osgtest.library.core as core
import osgtest.library.service as service
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import unittest

class TestStopGatekeeper(osgunittest.OSGTestCase):

    def test_01_stop_gatekeeper(self):
        core.skip_ok_unless_installed('globus-gatekeeper')
        self.skip_ok_unless(core.state['globus-gatekeeper.started-service'], 'did not start gatekeeper')

        files.restore(core.config['jobmanager-config'], 'globus')
        service.stop('globus-gatekeeper')

    def test_02_stop_seg(self):
        core.skip_ok_unless_installed('globus-scheduler-event-generator-progs')
        self.skip_ok_if(core.state['globus.started-seg'] == False, 'SEG apparently running')

        command = ('service', 'globus-scheduler-event-generator', 'stop')
        stdout, _, fail = core.check_system(command, 'Start Globus SEG')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(not os.path.exists(core.config['globus.seg-lockfile']),
                     'Globus SEG run lock file still present')
        core.state['globus.started-seg'] = False

    def test_03_configure_globus_pbs(self):
        self.skip_ok_unless(core.state['globus.pbs_configured'], 'Globus pbs configuration not altered')
        core.skip_ok_unless_installed('globus-gram-job-manager-pbs')
        files.restore(core.config['globus.pbs-config'], 'pbs')
