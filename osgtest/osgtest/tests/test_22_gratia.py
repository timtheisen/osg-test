import os
import pwd
import shutil
import socket
import stat
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.tomcat as tomcat
import osgtest.library.osgunittest as osgunittest

class TestStartGratia(osgunittest.OSGTestCase):

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


    # Carefully install a certificate with the given key from the given
    # source path, then set ownership and permissions as given.  Record
    # each directory and file created by this process into the config
    # dictionary; do so immediately after creation, so that the
    # remove_cert() function knows exactly what to remove/restore.
    def install_cert(self, target_key, source_key, owner_name, permissions):
        target_path = core.config[target_key]
        target_dir = os.path.dirname(target_path)
        source_path = core.config[source_key]
        user = pwd.getpwnam(owner_name)

        # Using os.path.lexists because os.path.exists return False for broken symlinks
        if os.path.lexists(target_path):
            backup_path = target_path + '.osgtest.backup'
            shutil.move(target_path, backup_path)
            core.state[target_key + '-backup'] = backup_path

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            core.state[target_key + '-dir'] = target_dir
            os.chown(target_dir, user.pw_uid, user.pw_gid)
            os.chmod(target_dir, 0755)

        shutil.copy(source_path, target_path)
        core.state[target_key] = target_path
        os.chown(target_path, user.pw_uid, user.pw_gid)
        os.chmod(target_path, permissions)

    # ==================================================================

    def test_01_config_certs(self):
        #=======================================================================
        # core.config['certs.hostcert'] = '/etc/grid-security/hostcert.pem'
        # core.config['certs.hostkey'] = '/etc/grid-security/hostkey.pem'
        #=======================================================================
        core.config['certs.httpcert'] = '/etc/grid-security/http/httpcert.pem'
        core.config['certs.httpkey'] = '/etc/grid-security/http/httpkey.pem'
        #=======================================================================
        # core.config['certs.vomscert'] = '/etc/grid-security/voms/vomscert.pem'
        # core.config['certs.vomskey'] = '/etc/grid-security/voms/vomskey.pem'
        #=======================================================================


    def test_02_install_http_certs(self):
        core.skip_ok_unless_installed('voms-admin-server')
        httpcert = core.config['certs.httpcert']
        httpkey = core.config['certs.httpkey']
        self.skip_ok_if(self.check_file_and_perms(httpcert, 'tomcat', 0644) and
                        self.check_file_and_perms(httpkey, 'tomcat', 0400),
                        'HTTP cert exists and has proper permissions')
        self.install_cert('certs.httpcert', 'certs.hostcert', 'tomcat', 0644)
        self.install_cert('certs.httpkey', 'certs.hostkey', 'tomcat', 0400)
        
        
#===============================================================================
#         9    Configure Gratia Service - service-authorization.properties    NO        modify /etc/gratia/collector/service-authorization.properties
# 10    Configure Gratia Service - service-configuration.properties     NO        modify /etc/gratia/collector/service-configuration.properties
# 11    Configure Gratia Service - install-database    NO        execute /usr/share/gratia/install-database
# 12    Configure Tomcat options    NO        "[root@gratia ~]$ cd /etc/grid-security
# [root@gratia ~]$ mkdir /etc/grid-security/http
# [root@gratia ~]$ cp hostcert.pem http/httpcert.pem
# [root@gratia ~]$ cp hostkey.pem http/httpkey.pem
# [root@gratia ~]$ chown -R tomcat:tomcat http"
#===============================================================================
