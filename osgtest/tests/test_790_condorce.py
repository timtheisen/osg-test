import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStopCondorCE(osgunittest.OSGTestCase):
    def test_01_stop_condorce(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client')
        self.skip_ok_unless(core.state['condor-ce.started-service'], 'did not start server')
        service.check_stop('condor-ce')

    def test_02_restore_config(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client')

        files.restore(core.config['condor-ce.condor-cfg'], 'condor-ce')
        files.restore(core.config['condor-ce.condor-ce-cfg'], 'condor-ce')
        if core.state['condor-ce.wrote-mapfile']:
            files.restore(core.config['condor-ce.mapfile'], 'condor-ce')
