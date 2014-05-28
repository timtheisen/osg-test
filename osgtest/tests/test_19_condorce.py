import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStartCondorCE(osgunittest.OSGTestCase):
    # Tests 01-02 are needed to reconfigure condor to work with HTCondor-CE
    def test_01_write_condor_config(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor')

        core.config['condor-ce.condor-cfg'] = '/etc/condor/config.d/99-osgtest.condor.conf'
        contents = """QUEUE_SUPER_USER_MAY_IMPERSONATE = .*
SCHEDD_INTERVAL=5
"""
        files.write(core.config['condor-ce.condor-cfg'],
                    contents,
                    owner='condor-ce',
                    chmod=0644)

    def test_02_reconfigure_condor(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor')
        self.skip_bad_unless(core.state['condor.running-service'], 'Condor not running')

        command = ('condor_reconfig', '-debug')
        core.check_system(command, 'Reconfigure Condor')
        self.assert_(os.path.exists(core.config['condor.lockfile']),
                     'Condor run lock file missing')

    def test_03_configure_condorce(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor')

        # Add hostname to the gridmap file and configure htcondor-ce to use it
        core.config['condor-ce.condor-ce-cfg'] = '/etc/condor-ce/config.d/99-osgtest.condor-ce.conf'
        condor_contents = "GRIDMAP = /etc/grid-security/grid-mapfile"
        files.write(core.config['condor-ce.condor-ce-cfg'],
                    condor_contents,
                    owner='condor-ce',
                    chmod=0644)

        core.config['condor-ce.lcmapsdb'] = '/etc/lcmaps.db'
        lcmaps_contents = """
authorize_only:
gridmapfile -> good | bad
"""
        files.append(core.config['condor-ce.lcmapsdb'], lcmaps_contents, owner='condor-ce')

        # Add host DN to condor_mapfile
        if core.options.hostcert:
            core.config['condor-ce.condorce_mapfile'] = '/etc/condor-ce/condor_mapfile'
            condor_mapfile_contents = files.read('/usr/share/osg-test/test_condorce_mapfile')
            files.write(core.config['condor-ce.condorce_mapfile'],
                        condor_mapfile_contents,
                        owner='condor-ce',
                        chmod=0644)

    def test_04_start_condorce(self):
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

