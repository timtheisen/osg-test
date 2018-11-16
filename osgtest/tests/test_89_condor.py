import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStopCondor(osgunittest.OSGTestCase):

    def test_01_stop_condor(self):
        core.skip_ok_unless_installed('condor')
        self.skip_ok_unless(core.state['condor.started-service'], 'did not start server')
        service.check_stop('condor')
        files.restore(core.config['condor.personal_condor'], 'condor')
        core.state['condor.running-service'] = False
