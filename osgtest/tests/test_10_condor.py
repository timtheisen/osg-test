import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStartCondor(osgunittest.OSGTestCase):

    def test_01_write_config(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client', 'htcondor-ce-condor')

        core.config['condor.condor-cfg'] = '/etc/condor/config.d/99-osgtest.conf'
        contents = """QUEUE_SUPER_USER_MAY_IMPERSONATE = vdttest
SCHEDD_INTERVAL=5
"""
        files.write(core.config['condor.condor-cfg'],
                    contents,
                    owner='condor',
                    chmod=0644)

    def test_02_start_condor(self):
        core.config['condor.lockfile'] = ''
        core.state['condor.started-service'] = False
        core.state['condor.running-service'] = False

        core.skip_ok_unless_installed('condor')

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
        core.state['condor.started-service'] = True
        core.state['condor.running-service'] = True
