import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStartCondorCE(osgunittest.OSGTestCase):
    # Tests 01-03 are needed to reconfigure condor to work with HTCondor-CE
    def test_01_stop_condor(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor')
        self.skip_ok_if(core.state['condor.running-service'] == False, 'did not start server')

        command = ('service', 'condor', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop Condor')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(not os.path.exists(core.config['condor.lockfile']),
                     'Condor run lock file still present')

        core.state['condor.running-service'] = False

    def test_02_write_condor_config(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor')

        core.config['condor-ce.condor-cfg'] = '/etc/condor/config.d/99-osgtest.condor.conf'
        contents = """QUEUE_SUPER_USER_MAY_IMPERSONATE = vdttest
SCHEDD_INTERVAL=5
"""
        files.write(core.config['condor-ce.condor-cfg'],
                    contents,
                    owner='condor-ce',
                    chmod=0644)

    def test_03_start_condor(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor')
        self.skip_bad_if(core.state['condor.running-service'], 'Running unconfigured Condor')

        core.config['condor.lockfile'] = ''

        # The name of the lockfile changed in 7.8.8
        condor_version = core.get_package_envra('condor')[2]
        condor_version_split = condor_version.split('.')
        if condor_version_split >= ['7', '8', '8']:
            core.config['condor.lockfile'] = '/var/lock/subsys/condor'
        else:
            core.config['condor.lockfile'] = '/var/lock/subsys/condor_master'

        if os.path.exists(core.config['condor.lockfile']):
            core.state['condor.running-service'] = True
            self.skip_ok('already running')

        command = ('service', 'condor', 'start')
        stdout, _, fail = core.check_system(command, 'Start Condor')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['condor.lockfile']),
                     'Condor run lock file missing')
        core.state['condor.running-service'] = True

    def test_04_configure_gridmapfile(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor')

        core.config['condor-ce.condor-ce-cfg'] = '/etc/condor-ce/config.d/99-osgtest.condor-ce.conf'
        condor_contents = "GRIDMAP = /etc/grid-security/grid-mapfile"
        files.write(core.config['condor-ce.condor-ce-cfg'],
                    condor_contents,
                    owner='condor-ce',
                    chmod=0644)

        core.config['condor-ce.lcmapsdb'] = '/etc/lcmaps.db'
        lcmaps_contents = """authorize_only:
gridmapfile -> good | bad
"""
        files.append(core.config['condor-ce.lcmapsdb'], lcmaps_contents, owner='condor-ce')

    def test_05_start_condorce(self):
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

