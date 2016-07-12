import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest

class TestSetupVomsAdmin(osgunittest.OSGTestCase):

    def test_01_open_access(self):
        core.state['voms-admin.read-members'] = False
        core.skip_ok_unless_installed('voms-admin-server', 'voms-admin-client')
        self.skip_bad_unless(core.state['tomcat.started'], 'Tomcat not started')

        command = ('voms-admin', '--nousercert', '--vo', core.config['voms.vo'], 'add-ACL-entry',
                   '/' + core.config['voms.vo'], 'ANYONE', 'VOMS_CA', 'CONTAINER_READ,MEMBERSHIP_READ', 'true')
        core.check_system(command, 'Add VOMS Admin ACL entry')
        core.state['voms-admin.read-members'] = True
