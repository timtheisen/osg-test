import os
import re
import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest

class TestCondorCE(osgunittest.OSGTestCase):
    def general_requirements(self):
        self.skip_ok_unless('condor-ce.started', 'ce not running')
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor', 'lcmaps',
                                      'lcas-lcmaps-gt4-interface')  

    def test_01_status(self):
        self.general_requirements()

        command = ('condor_ce_status', '-verbose')
        core.check_system(command, 'ce status', user=True)

    def test_02_queue(self):
        self.general_requirements()
        
        command = ('condor_ce_q', '-verbose')
        core.check_system(command, 'ce queue', user=True)
        
    def test_03_ping(self):
        self.general_requirements()

        command = ('env', '_condor_SEC_CLIENT_AUTHENTICATION_METHODS=GSI', 'condor_ce_ping', 'WRITE', '-verbose')
        stdout, _, _ = core.check_system(command, 'ping using GSI and gridmap', user=True)
        self.assert_(re.search('Authorized:\s*TRUE', stdout), 'could not authorize with GSI')

    def test_04_trace(self):
        self.general_requirements()

        cwd = os.getcwd()
        os.chdir('/tmp')
        
        command = ('condor_ce_trace', '--debug', core.get_hostname())
        core.check_system(command, 'ce trace', user=True)

        os.chdir(cwd)
