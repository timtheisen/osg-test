import osgtest.library.core as core
import osgtest.library.condor as condor
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStartCondor(osgunittest.OSGTestCase):

    def test_01_start_condor(self):
        core.state['condor.running-service'] = False

        core.skip_ok_unless_installed('condor')
        core.config['condor.collectorlog'] = condor.config_val('COLLECTOR_LOG')

        if service.is_running('condor'):
            core.state['condor.running-service'] = True
            return

        core.config['condor.collectorlog_stat'] = core.get_stat(core.config['condor.collectorlog'])

        service.check_start('condor')
        core.state['condor.started-service'] = True
        core.state['condor.running-service'] = True
