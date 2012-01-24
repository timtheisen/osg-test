import os
import osgtest.library.core as core
import pwd
import shutil
import socket
import unittest

class TestStartVOMS(unittest.TestCase):

    # "Constants"


    # Class attributes
    __started_voms = False
    __started_voms_admin = False
    __installed_vomses = False

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

        if os.path.exists(target_path):
            backup_path = target_path + '.osgtest.backup'
            shutil.move(target_path, backup_path)
            core.state[target_key + '-backup'] = backup_path

        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
            core.state[target_key + '-dir'] = target_dir
            os.chown(target_dir, user.pw_uid, user.pw_gid)
            os.chmod(target_dir, 0755)

        shutil.copy(source_path, target_path)
        core.state[target_key] = target_path
        os.chown(target_path, user.pw_uid, user.pw_gid)
        os.chmod(target_path, permissions)

    # ==================================================================

    def test_01_config_certs(self):
        core.config['certs.hostcert'] = '/etc/grid-security/hostcert.pem'
        core.config['certs.hostkey'] = '/etc/grid-security/hostkey.pem'
        core.config['certs.httpcert'] = '/etc/grid-security/http/httpcert.pem'
        core.config['certs.httpkey'] = '/etc/grid-security/http/httpkey.pem'
        core.config['certs.vomscert'] = '/etc/grid-security/voms/vomscert.pem'
        core.config['certs.vomskey'] = '/etc/grid-security/voms/vomskey.pem'

    def test_02_install_voms_certs(self):
        if not core.rpm_is_installed('voms-server'):
            core.skip('VOMS not installed')
            return
        if (os.path.exists(core.config['certs.vomscert']) and
            os.path.exists(core.config['certs.vomskey'])):
            core.skip('VOMS cert exists')
            return
        self.install_cert('certs.vomscert', 'certs.hostcert', 'voms', 0644)
        self.install_cert('certs.vomskey', 'certs.hostkey', 'voms', 0400)

    def test_03_install_http_certs(self):
        if not core.rpm_is_installed('voms-admin-server'):
            core.skip('VOMS Admin not installed')
            return
        if (os.path.exists(core.config['certs.httpcert']) and
            os.path.exists(core.config['certs.httpkey'])):
            core.skip('HTTP cert exists')
            return
        self.install_cert('certs.httpcert', 'certs.hostcert', 'tomcat', 0644)
        self.install_cert('certs.httpkey', 'certs.hostkey', 'tomcat', 0400)

    def test_04_config_voms(self):
        core.config['voms.vo'] = 'osgtestvo'
        core.config['voms.lsc-dir'] = '/etc/grid-security/vomsdir/osgtestvo'
        core.config['voms.lock-file'] = '/var/lock/subsys/voms.osgtestvo'
        core.config['voms.vo-webapp'] = ('/usr/share/tomcat5/conf/Catalina/' +
                                         'localhost/voms#osgtestvo.xml')
        core.config['voms.webapp-log'] = ('/var/log/tomcat5/' +
                                          'voms-admin-osgtestvo.log')

    def test_05_configure_voms_admin(self):
        if core.missing_rpm('voms-admin-server', 'voms-mysql-plugin'):
            return

        # Find full path to libvomsmysql.so
        command = ('rpm', '--query', '--list', 'voms-mysql-plugin')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('List VOMS-MySQL files', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        voms_mysql_files = stdout.strip().split('\n')
        voms_mysql_so_path = None
        for voms_mysql_path in voms_mysql_files:
            if 'libvomsmysql.so' in voms_mysql_path:
                voms_mysql_so_path = voms_mysql_path
        self.assert_(voms_mysql_so_path is not None,
                     'Could not find VOMS MySQL shared library path')
        self.assert_(os.path.exists(voms_mysql_so_path),
                     'VOMS MySQL shared library path does not exist')

        # Configure VOMS Admin with new VO
        db_user_name = 'admin-' + core.config['voms.vo']
        command = ('voms-admin-configure', 'install',
                   '--vo', core.config['voms.vo'],
                   '--dbtype', 'mysql', '--createdb', '--deploy-database',
                   '--dbauser', 'root', '--dbapwd', '', '--dbport', '3306',
                   '--dbusername', db_user_name, '--dbpassword', 'secret',
                   '--port', '15151', '--sqlloc', voms_mysql_so_path,
                   '--mail-from', 'root@localhost', '--smtp-host', 'localhost',
                   '--cert', core.config['certs.vomscert'],
                   '--key', core.config['certs.vomskey'],
                   '--read-access-for-authenticated-clients')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Configure VOMS Admin', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        good_message = 'VO %s installation finished' % (core.config['voms.vo'])
        self.assert_(good_message in stdout, fail)

    def test_06_add_local_admin(self):
        if core.missing_rpm('voms-admin-server', 'voms-mysql-plugin'):
            return
        host_dn, host_issuer = \
            core.certificate_info(core.config['certs.hostcert'])
        command = ('voms-db-deploy.py', 'add-admin',
                   '--vo', core.config['voms.vo'],
                   '--dn', host_dn, '--ca', host_issuer)
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Add VO admin', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    def test_07_config_va_properties(self):
        if core.missing_rpm('voms-admin-server'):
            return

        properties_path = os.path.join('/etc/voms-admin',
                                       core.config['voms.vo'],
                                       'voms.service.properties')
        new_path = properties_path + '__NEW'
        properties_file = open(properties_path, 'r')
        new_file = open(new_path, 'w')
        wrote_csrf_line = False
        for line in properties_file:
            if 'voms.csrf.log_only' in line:
                new_file.write('voms.csrf.log_only = true\n')
                wrote_csrf_line = True
            else:
                new_file.write(line.rstrip('\n') + '\n')
        properties_file.close()
        if not wrote_csrf_line:
            new_file.write('voms.csrf.log_only = true\n')
        new_file.close()
        shutil.move(new_path, properties_path)

    def test_08_advertise(self):
        core.state['voms.installed-vomses'] = False

        if core.missing_rpm('voms-admin-server'):
            return

        if os.path.exists('/etc/vomses'):
            shutil.move('/etc/vomses', '/etc/vomses.osg-test.backup')

        hostname = socket.getfqdn()
        host_dn, host_issuer = \
            core.certificate_info(core.config['certs.hostcert'])
        vomses = open('/etc/vomses', 'w')
        vomses.write('"%s" "%s" "%d" "%s" "%s"\n' %
                     (core.config['voms.vo'], hostname, 15151, host_dn,
                      core.config['voms.vo']))
        vomses.close()
        core.state['voms.installed-vomses'] = True

        if not os.path.isdir(core.config['voms.lsc-dir']):
            os.mkdir(core.config['voms.lsc-dir'])
        vo_lsc_path = os.path.join(core.config['voms.lsc-dir'],
                                   hostname + '.lsc')
        vo_lsc_file = open(vo_lsc_path, 'w')
        vo_lsc_file.write(host_dn + '\n')
        vo_lsc_file.write(host_issuer + '\n')
        vo_lsc_file.close()

        core.syspipe('ls -ldF /etc/*vom*', shell=True)
        core.syspipe(('find', '/etc/grid-security/vomsdir', '-ls'))

    def test_09_start_voms(self):
        core.state['voms.started-server'] = False

        if not core.rpm_is_installed('voms-server'):
            core.skip('not installed')
            return
        if os.path.exists(core.config['voms.lock-file']):
            core.skip('apparently running')
            return

        command = ('service', 'voms', 'start')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Start VOMS service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(os.path.exists(core.config['voms.lock-file']),
                     'VOMS server PID file is missing')
        core.state['voms.started-server'] = True

    def test_10_install_vo_webapp(self):
        core.state['voms.installed-vo-webapp'] = False
        if not core.rpm_is_installed('voms-admin-server'):
            core.skip('not installed')
            return
        if os.path.exists(core.config['voms.vo-webapp']):
            core.skip('apparently installed')
            return

        command = ('service', 'voms-admin', 'start')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Start VOMS Admin service', status, stdout,
                             stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(os.path.exists(core.config['voms.vo-webapp']),
                     'VOMS Admin VO context file is missing')
        core.state['voms.installed-vo-webapp'] = True
