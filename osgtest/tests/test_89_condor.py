import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStopCondor(osgunittest.OSGTestCase):

    def test_01_stop_condor(self):
        core.skip_ok_unless_installed('condor')
        self.skip_ok_if(core.state['condor.started-service'] == False, 'did not start server')

        command = ('service', 'condor', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop Condor')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(not os.path.exists(core.config['condor.lockfile']),
                     'Condor run lock file still present')

        core.state['condor.running-service'] = False

    def test_02_restore_config(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor')        

        files.restore(core.config['condor.condor-cfg'], 'condor')
