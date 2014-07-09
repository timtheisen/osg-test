import os
import pwd
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.certificates as certs

class TestGUMS(osgunittest.OSGTestCase):

    required_rpms = ['gums-service',
                     'gums-client']

    def get_user_dn(self, username):
        pwd_entry = pwd.getpwnam(username)
        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_dn, _ = certs.certificate_info(cert_path)
        return user_dn

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

    def test_02_manual_group_add(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        core.state['gums.added_user'] = False

        user_dn = self.get_user_dn(core.options.username)
        # If we have a VO set up, use it
        if core.state['voms.added-user']:
            command = ('gums-service', 'manualGroupAdd',
                       '--fqan', '/%s/Role=null/Capability=null' % core.config['voms.vo'],
                       'gums-test', user_dn)
        else:
            command = ('gums-service', 'manualGroupAdd', 'gums-test', user_dn)

        stdout = core.check_system(command, 'Add VDT DN to manual group')[0]
        core.state['gums.added_user'] = True

    def test_03_map_user(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_bad_unless(core.state['gums.added_user'] == True, 'User not added to manual user group')
      
        user_dn = self.get_user_dn(core.options.username)
        # Use gums-host since it defaults to the host cert
        if core.state['voms.added-user']:
            command = ('gums-host', 'mapUser',
                       '--fqan', '/%s/Role=null/Capability=null' % core.config['voms.vo'],
                       user_dn) 
        else:
            command = ('gums-host', 'mapUser', user_dn)
            
        stdout = core.check_system(command, 'Map GUMS user')[0]
        self.assert_(core.options.username in stdout, 'expected string missing from mapUser output')

    def test_04_generate_mapfile(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_bad_unless(core.state['gums.added_user'] == True, 'User not added to manual user group')

        user_dn = self.get_user_dn(core.options.username)
        if core.state['voms.added-user']:
            command = ('gums-host', 'generateVoGridMapfile')
        else:
            command = ('gums-host', 'generateGridMapfile')
        stdout = core.check_system(command, 'generate grid mapfile')[0]
        self.assert_(user_dn in stdout, 'user DN missing from generated mapfile')
        
    def test_05_unset_x509_env(self):
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
