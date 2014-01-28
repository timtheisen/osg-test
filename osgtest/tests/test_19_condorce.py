import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStartCondorCE(osgunittest.OSGTestCase):
    def test_01_write_mapfile(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor')
        core.config['condor-ce.mapfile'] = '/etc/condor-ce/condor_mapfile'
        contents = 'GSI "^%s.*" vdttest' % core.config['user.cert_subject'] + \
            """
GSI "^\/DC\=org\/DC\=doegrids\/OU\=Services\/CN\=(host\/)?([A-Za-z0-9.\-]*)$" \\2@daemon.opensciencegrid.org
GSI "^\/DC\=com\/DC\=DigiCert-Grid\/O=Open Science Grid\/OU\=Services\/CN\=(host\/)?([A-Za-z0-9.\-]*)$" \\2@daemon.opensciencegrid.org
GSI (.*) GSS_ASSIST_GRIDMAP
GSI (.*) anonymous@gsi
CLAIMTOBE .* anonymous@claimtobe
FS (.*) \\1"""
        
        files.write(core.config['condor-ce.mapfile'], contents, owner='condor-ce')

    def test_02_start_condorce(self):
        core.config['condor-ce.lockfile'] = '/var/lock/subsys/condor-ce'
        core.state['condor-ce.started'] = False
        
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor')
        self.skip_ok_if(os.path.exists(core.config['condor-ce.lockfile']), 'already running')

        command = ('service', 'condor-ce', 'start')
        stdout, _, fail = core.check_system(command, 'Start HTCondor CE')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(os.path.exists(core.config['condor-ce.lockfile']),
                     'HTCondor CE run lock file missing')
        core.state['condor-ce.started'] = True

