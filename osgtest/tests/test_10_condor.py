import os
import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStartCondor(osgunittest.OSGTestCase):

    def test_01_start_condor(self):
        core.state['condor.running-service'] = False

        core.skip_ok_unless_installed('condor')
        core.config['condor.collectorlog'] = core.check_system(('condor_config_val', 'COLLECTOR_LOG'),
                                                               'Failed to query for Condor CollectorLog path')[0]\
                                                 .strip()

        if service.is_running('condor'):
            core.state['condor.running-service'] = True
            return

        try:
            core.config['condor.collectorlog_stat'] = os.stat(core.config['condor.collectorlog'])
        except OSError:
            core.config['condor.collectorlog_stat'] = None

        service.start('condor')
        self.assert_(service.is_running('condor'), 'Condor not running after we started it')
        core.state['condor.started-service'] = True
        core.state['condor.running-service'] = True
