import osgtest.library.core as core
import osgtest.library.service as service
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest


class TestStopGatekeeper(osgunittest.OSGTestCase):

    def test_01_stop_gatekeeper(self):
        core.skip_ok_unless_installed('globus-gatekeeper')
        self.skip_ok_unless(core.state['globus-gatekeeper.started-service'], 'did not start gatekeeper')

        files.restore(core.config['jobmanager-config'], 'globus')
        service.check_stop('globus-gatekeeper')

    def test_02_stop_seg(self):
        core.skip_ok_unless_installed('globus-scheduler-event-generator-progs')
        self.skip_ok_if(core.state['globus.started-seg'] == False, 'SEG apparently running')
        service.check_stop('globus-scheduler-event-generator')

    def test_03_configure_globus_pbs(self):
        self.skip_ok_unless(core.state['globus.pbs_configured'], 'Globus pbs configuration not altered')
        core.skip_ok_unless_installed('globus-gram-job-manager-pbs')
        files.restore(core.config['globus.pbs-config'], 'pbs')
