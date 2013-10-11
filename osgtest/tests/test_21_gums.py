import os
import pwd
import re
import socket
import stat
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.certificates as certs

class TestStartGUMS(osgunittest.OSGTestCase):

    # ==========================================================================
    # START: (MOSTLY) COPIED FROM test_20_voms.py
    # Should be refactored, but I am in a hurry!!!
    # ==========================================================================

    def check_file_and_perms(self, file_path, owner_name, permissions):
        """Return True if the file at 'file_path' exists, is owned by
        'owner_name', is a file, and has the given permissions; False otherwise

        """
        owner_uid = pwd.getpwnam(owner_name)
        try:
            file_stat = os.stat(file_path)
            return (file_stat.st_uid == owner_uid and
                    file_stat.st_mode & 07777 == permissions and
                    stat.S_ISREG(file_stat.st_mode))
        except OSError: # file does not exist
            return False

    def test_01_config_certs(self):
        core.config['certs.hostcert'] = '/etc/grid-security/hostcert.pem'
        core.config['certs.hostkey'] = '/etc/grid-security/hostkey.pem'
        core.config['certs.httpcert'] = '/etc/grid-security/http/httpcert.pem'
        core.config['certs.httpkey'] = '/etc/grid-security/http/httpkey.pem'

    def test_02_install_http_certs(self):
        core.skip_ok_unless_installed('gums-service')
        httpcert = core.config['certs.httpcert']
        httpkey = core.config['certs.httpkey']
        self.skip_ok_if(self.check_file_and_perms(httpcert, 'tomcat', 0644) and
                        self.check_file_and_perms(httpkey, 'tomcat', 0400),
                        'HTTP cert exists and has proper permissions')
        certs.install_cert('certs.httpcert', 'certs.hostcert', 'tomcat', 0644)
        certs.install_cert('certs.httpkey', 'certs.hostkey', 'tomcat', 0400)

    # ==========================================================================
    # END: (MOSTLY) COPIED FROM test_20_voms.py
    # ==========================================================================

    def test_03_gums_configuration(self):
        core.config['gums.password'] = 'osgGUMS!'

    def test_04_setup_gums_database(self):
        core.skip_ok_unless_installed('gums-service')
        command = ('gums-setup-mysql-database', '--noprompt', '--user', 'gums', '--host', 'localhost:3306',
                   '--password', core.config['gums.password'])
        stdout = core.check_system(command, 'Set up GUMS MySQL database')[0]
        self.assert_('ERROR' not in stdout,
                     'gums-setup-mysql-database failure message')

    def test_05_add_mysql_admin(self):
        core.skip_ok_unless_installed('gums-service')
        host_dn, host_issuer = certs.certificate_info(core.config['certs.hostcert'])
        mysql_template_path = '/usr/lib/gums/sql/addAdmin.mysql'
        self.assert_(os.path.exists(mysql_template_path), 'GUMS MySQL template exists')
        mysql_template = files.read(mysql_template_path, as_single_string=True).strip()
        core.log_message(mysql_template)

        mysql_command = re.sub(r'@ADMINDN@', host_dn, mysql_template)
        core.log_message(mysql_command)

        command = ('mysql', '--user=gums', '-p' + core.config['gums.password'], '--execute=' + mysql_command)
        core.check_system(command, 'Could not add GUMS MySQL admin')

