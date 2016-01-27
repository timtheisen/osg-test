import cagen
import os
import re
import socket
import stat
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStartGUMS(osgunittest.OSGTestCase):

    # ==========================================================================
    # START: (MOSTLY) COPIED FROM test_20_voms.py
    # Should be refactored, but I am in a hurry!!!
    # ==========================================================================

    core.config['gums.password'] = 'osgGUMS!'
    
    def test_01_config_certs(self):
        core.config['certs.httpcert'] = '/etc/grid-security/http/httpcert.pem'
        core.config['certs.httpkey'] = '/etc/grid-security/http/httpkey.pem'

    def test_02_install_http_certs(self):
        core.skip_ok_unless_installed('gums-service')
        httpcert = core.config['certs.httpcert']
        httpkey = core.config['certs.httpkey']
        self.skip_ok_if(core.check_file_and_perms(httpcert, 'tomcat', 0644) and
                        core.check_file_and_perms(httpkey, 'tomcat', 0400),
                        'HTTP cert exists and has proper permissions')
        core.install_cert('certs.httpcert', 'certs.hostcert', 'tomcat', 0644)
        core.install_cert('certs.httpkey', 'certs.hostkey', 'tomcat', 0400)

    # ==========================================================================
    # END: (MOSTLY) COPIED FROM test_20_voms.py
    # ==========================================================================

    def test_03_setup_gums_database(self):
        core.skip_ok_unless_installed('gums-service')
        command = ('gums-setup-mysql-database', '--noprompt', '--user', 'gums', '--host', 'localhost:3306',
                   '--password', core.config['gums.password'])
        stdout = core.check_system(command, 'Set up GUMS MySQL database')[0]
        self.assert_('ERROR' not in stdout,
                     'gums-setup-mysql-database failure message')

    def test_04_add_mysql_admin(self):
        core.skip_ok_unless_installed('gums-service')
        host_dn, _ = cagen.certificate_info(core.config['certs.hostcert'])
        mysql_template_path = '/usr/lib/gums/sql/addAdmin.mysql'
        self.assert_(os.path.exists(mysql_template_path), 'GUMS MySQL template exists')
        mysql_template = files.read(mysql_template_path, as_single_string=True).strip()
        core.log_message(mysql_template)

        mysql_command = re.sub(r'@ADMINDN@', host_dn, mysql_template)
        core.log_message(mysql_command)

        command = ('mysql', '--user=gums', '-p' + core.config['gums.password'], '--execute=' + mysql_command)
        core.check_system(command, 'Could not add GUMS MySQL admin')

    def test_05_gums_configuration(self):
        core.skip_ok_unless_installed('gums-service')
        core.config['gums.config-file'] = '/etc/gums/gums.config'

        files.replace(core.config['gums.config-file'],
                      '			accountName=\'GumsTestUserMappingSuccessful\'/>',
                      "			accountName=\'" + core.options.username + "\'/>",
                      owner='gums')
        
