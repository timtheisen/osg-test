import cagen
import os

import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest

class TestGUMS(osgunittest.OSGTestCase):

    required_rpms = ['gums-service',
                     'gums-client']

    def test_01_set_x509_env(self):
        core.skip_ok_unless_installed(*self.required_rpms)

        try:
            core.config['gums.old_x509_cert'] = os.environ['X509_USER_CERT']
        except KeyError:
            # X509_USER_CERT isn't defined
            pass

        try:
            core.config['gums.old_x509_key'] = os.environ['X509_USER_KEY']
        except KeyError:
            # X509_USER_KEY isn't defined
            pass

        os.putenv('X509_USER_CERT', '/etc/grid-security/hostcert.pem')
        os.putenv('X509_USER_KEY', '/etc/grid-security/hostkey.pem')

    def test_02_server_version(self):
        core.skip_ok_unless_installed(*self.required_rpms)

        stdout = core.check_system(('gums-host', 'serverVersion'), 'Query GUMS server version')[0]
        self.assert_("GUMS server version" in stdout, "expected string missing from serverVersion output")

    def test_03_manual_group_add(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        core.state['gums.added_user'] = False

        # If we have a VO set up, use it
        if core.state['voms.added-user']:
            command = ('gums-service', 'manualGroupAdd',
                       '--fqan', '/%s/Role=null/Capability=null' % core.config['voms.vo'],
                       'gums-test', core.config['user.cert_subject'])
        else:
            command = ('gums-service', 'manualGroupAdd', 'gums-test', core.config['user.cert_subject'])

        core.check_system(command, 'Add VDT DN to manual group')
        core.state['gums.added_user'] = True

    def test_04_map_user(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_bad_unless(core.state['gums.added_user'] == True, 'User not added to manual user group')

        # Use gums-host since it defaults to the host cert
        if core.state['voms.added-user']:
            command = ('gums-host', 'mapUser',
                       '--fqan', '/%s/Role=null/Capability=null' % core.config['voms.vo'],
                       core.config['user.cert_subject'])
        else:
            command = ('gums-host', 'mapUser', core.config['user.cert_subject'])

        stdout = core.check_system(command, 'Map GUMS user')[0]
        self.assert_(core.options.username in stdout, 'expected string missing from mapUser output')

    def test_05_generate_mapfile(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_bad_unless(core.state['gums.added_user'] == True, 'User not added to manual user group')

        if core.state['voms.added-user']:
            command = ('gums-host', 'generateVoGridMapfile')
        else:
            command = ('gums-host', 'generateGridMapfile')
        stdout = core.check_system(command, 'generate grid mapfile')[0]
        self.assert_(core.config['user.cert_subject'] in stdout, 'user DN missing from generated mapfile')

    def test_06_unset_x509_env(self):
        core.skip_ok_unless_installed(*self.required_rpms)

        try:
            os.putenv('X509_USER_CERT', core.config['gums.old_x509_cert'])
        except KeyError:
            # If the core.config value isn't there, there was no original $X509_USER_CERT
            os.unsetenv('X509_USER_CERT')

        try:
            os.putenv('X509_USER_KEY', core.config['gums.old_x509_key'])
        except KeyError:
            # If the core.config value isn't there, there was no original $X509_USER_KEY
            os.unsetenv('X509_USER_KEY')
