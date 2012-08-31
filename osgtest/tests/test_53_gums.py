import os
import pwd
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.tomcat as tomcat

class TestGUMS(unittest.TestCase):

    def test_01_map_user(self):
        if core.missing_rpm('gums-service'):
            return

        host_dn, _ = core.certificate_info(core.config['certs.hostcert'])
        pwd_entry = pwd.getpwnam(core.options.username)
        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_dn, _ = core.certificate_info(cert_path)
        command = ('gums', 'mapUser', '--service', host_dn, user_dn)
        core.check_system(command, 'Map GUMS user')
