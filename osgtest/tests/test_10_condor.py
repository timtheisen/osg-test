import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.condor as condor


class TestStartCondor(osgunittest.OSGTestCase):

    def test_01_start_condor(self):
        core.state['condor.running-service'] = False

        core.skip_ok_unless_installed('condor')
        core.config['condor.collectorlog'] = core.check_system(('condor_config_val', 'COLLECTOR_LOG'),
                                                               'Failed to query for Condor CollectorLog path')[0]\
                                                 .strip()

        if condor.is_running():
            core.state['condor.running-service'] = True
            self.skip_ok('already running')

        command = ('service', 'condor', 'start')
        stdout, _, fail = core.check_system(command, 'Start Condor')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(condor.is_running(), 'Condor not running after we started it')
        core.state['condor.running-service'] = True

        try:
            core.config['condor.collectorlog_stat'] = os.stat(core.config['condor.collectorlog'])
        except OSError:
            core.config['condor.collectorlog_stat'] = None
