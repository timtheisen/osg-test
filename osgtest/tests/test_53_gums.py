import os
import pwd
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestGUMS(osgunittest.OSGTestCase):

    def test_01_manual_group_add(self):
        core.skip_ok_unless_installed('gums-service')

        core.state['gums.added_user'] = False

        pwd_entry = pwd.getpwnam(core.options.username)
        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_dn, _ = core.certificate_info(cert_path)
        
        command = ('env')
        core.system(command, shell=True)
        
        command = ('gums-service', 'manualGroupAdd', 'gums-test', user_dn)
        stdout = core.check_system(command, 'Add VDT DN to manual group')[0]
        core.state['gums.added_user'] = True

    def test_02_map_user(self):
        core.skip_ok_unless_installed('gums-service')
        self.skip_bad_unless(core.state['gums.added_user'] == True, 'User not added to manualUserGroup')
        
        host_dn, _ = core.certificate_info(core.config['certs.hostcert'])
        pwd_entry = pwd.getpwnam(core.options.username)
        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_dn, _ = core.certificate_info(cert_path)
        command = ('gums-host', 'mapUser', user_dn) # using gums-host since it defaults to the host cert
        stdout = core.check_system(command, 'Map GUMS user')[0]
        self.assert_('GumsTestUserMappingSuccessful' in stdout)
