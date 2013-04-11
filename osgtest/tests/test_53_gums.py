import os
import pwd
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.tomcat as tomcat
import osgtest.library.osgunittest as osgunittest

class TestGUMS(osgunittest.OSGTestCase):

    def test_01_map_user(self):
        core.skip_ok_unless_installed('gums-service')

        host_dn, _ = core.certificate_info(core.config['certs.hostcert'])
        pwd_entry = pwd.getpwnam(core.options.username)
        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_dn, _ = core.certificate_info(cert_path)
        command = ('gums', 'mapUser', '--service', host_dn, user_dn)
        core.check_system(command, 'Map GUMS user')
