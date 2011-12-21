import glob
import os
import osgtest
import pwd
import re
import shutil
import socket
import time
import unittest

class TestVOMS(unittest.TestCase):

    # "Constants"
    __voname = 'osgtestvo'
    __sentinel_mysqld = '/var/run/mysqld/mysqld.pid'
    __sentinel_voms = '/var/lock/subsys/voms.' + __voname
    __sentinel_tomcat = '/var/run/tomcat5.pid'
    __sentinel_voms_admin = '/usr/share/tomcat5/conf/Catalina/localhost/' + \
        'voms#' + __voname + '.xml'
    __vomsadmin_logfile = '/var/log/tomcat5/voms-admin-%s.log' % (__voname)
    __vomsadmin_log_start = 0
    __vo_lsc_dir = os.path.join('/etc/grid-security/vomsdir', __voname)
    __hostcert = '/etc/grid-security/hostcert.pem'
    __hostkey = '/etc/grid-security/hostkey.pem'
    __mkgridmap_conf = '/usr/share/osg-test/edg-mkgridmap.conf'


    # Certificate stuff
    __certs = {}
    __certs['vomscert'] = '/etc/grid-security/voms/vomscert.pem'
    __certs['vomskey'] = '/etc/grid-security/voms/vomskey.pem'
    __certs['httpcert'] = '/etc/grid-security/http/httpcert.pem'
    __certs['httpkey'] = '/etc/grid-security/http/httpkey.pem'

    # Class attributes
    __started_mysqld = False
    __started_voms = False
    __started_tomcat = False
    __started_voms_admin = False
    __installed_vomscert = False
    __installed_vomses = False
    __got_proxy = False

    # Carefully install a certificate with the given nickname from the given
    # source path, then set ownership and permissions as given.  Record each
    # directory and file created by this process into the TestVOMS.__certs
    # dictionary; do so immediately after creation, so that the remove_cert()
    # function knows exactly what to remove/restore.
    def install_cert(self, nickname, source_path, owner_name, permissions):
        target_path = TestVOMS.__certs[nickname]
        target_dir = os.path.dirname(target_path)
        user = pwd.getpwnam(owner_name)

        if os.path.exists(target_path):
            backup_path = target_path + '.osgtest-backup'
            shutil.move(target_path, backup_path)
            TestVOMS.__certs[nickname + '_backup'] = backup_path

        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
            TestVOMS.__certs[nickname + '_dir'] = target_dir
            os.chown(target_dir, user.pw_uid, user.pw_gid)
            os.chmod(target_dir, 0755)

        shutil.copy(source_path, target_path)
        TestVOMS.__certs[nickname + '_path'] = target_path
        os.chown(target_path, user.pw_uid, user.pw_gid)
        os.chmod(target_path, permissions)

    # Carefully remove a certificate identified by the given nickname.  Remove
    # all paths associated with the nickname that were logged into the __certs
    # dictionary, as they were created by the install_cert() function.
    def remove_cert(self, nickname):
        if TestVOMS.__certs.has_key(nickname + '_path'):
            os.remove(TestVOMS.__certs[nickname + '_path'])
        if TestVOMS.__certs.has_key(nickname + '_backup'):
            shutil.move(TestVOMS.__certs[nickname + '_backup'],
                        TestVOMS.__certs[nickname])
        if TestVOMS.__certs.has_key(nickname + '_dir'):
            target_dir = TestVOMS.__certs[nickname + '_dir']
            if len(os.listdir(target_dir)) == 0:
                os.rmdir(target_dir)

    # ==========================================================================

    def test_01_start_mysqld(self):
        TestVOMS.__started_mysqld = False
        if not osgtest.rpm_is_installed('mysql-server'):
            osgtest.skip('not installed')
            return
        if os.path.exists(TestVOMS.__sentinel_mysqld):
            osgtest.skip('apparently running')
            return
        command = ('service', 'mysqld', 'start')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Start MySQL service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(os.path.exists(TestVOMS.__sentinel_mysqld),
                     'MySQL server PID file is missing')
        TestVOMS.__started_mysqld = True

    def test_02_install_voms_certs(self):
        if osgtest.rpm_is_installed('voms-server'):
            if not (os.path.exists(TestVOMS.__certs['vomscert']) and \
                    os.path.exists(TestVOMS.__certs['vomskey'])):
                self.install_cert('vomscert', TestVOMS.__hostcert, 'voms', 0644)
                self.install_cert('vomskey', TestVOMS.__hostkey, 'voms', 0400)
            else:
                osgtest.skip('VOMS cert exists')
        else:
            osgtest.skip('VOMS not installed')

    def test_03_install_http_certs(self):
        if osgtest.rpm_is_installed('voms-admin-server'):
            if not (os.path.exists(TestVOMS.__certs['httpcert']) and \
                    os.path.exists(TestVOMS.__certs['httpkey'])):
                self.install_cert('httpcert', TestVOMS.__hostcert, 'tomcat', 0644)
                self.install_cert('httpkey', TestVOMS.__hostkey, 'tomcat', 0400)
            else:
                osgtest.skip('HTTP cert exists')
        else:
            osgtest.skip('VOMS Admin not installed')

    def test_04_config_voms_admin(self):
        if osgtest.missing_rpm('voms-admin-server', 'voms-mysql-plugin'):
            return

        # Find full path to libvomsmysql.so
        command = ('rpm', '--query', '--list', 'voms-mysql-plugin')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('List VOMS/MySQL files', status, stdout, stderr)
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
        db_user_name = 'admin-' + TestVOMS.__voname
        command = ('voms-admin-configure', 'install', '--vo', TestVOMS.__voname,
                   '--dbtype', 'mysql', '--createdb', '--deploy-database',
                   '--dbauser', 'root', '--dbapwd', '', '--dbport', '3306',
                   '--dbusername', db_user_name, '--dbpassword', 'secret',
                   '--port', '15151', '--sqlloc', voms_mysql_so_path,
                   '--mail-from', 'root@localhost', '--smtp-host', 'localhost',
                   '--cert', TestVOMS.__certs['vomscert'],
                   '--key', TestVOMS.__certs['vomskey'],
                   '--read-access-for-authenticated-clients')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Configure VOMS Admin', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        good_message = 'VO %s installation finished' % (TestVOMS.__voname)
        self.assert_(good_message in stdout, fail)

    def test_05_add_local_admin(self):
        if osgtest.missing_rpm('voms-admin-server', 'voms-mysql-plugin'):
            return
        host_dn, host_issuer = osgtest.certificate_info(TestVOMS.__hostcert)
        command = ('voms-db-deploy.py', 'add-admin', '--vo', TestVOMS.__voname,
                   '--dn', host_dn, '--ca', host_issuer)
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Add VO admin', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    def test_06_config_trustmanager(self):
        if osgtest.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return

        command = (('/var/lib/trustmanager-tomcat/configure.sh',))
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Config trustmanager', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    def test_07_config_va_properties(self):
        if osgtest.missing_rpm('voms-admin-server'):
            return

        properties_path = os.path.join('/etc/voms-admin', TestVOMS.__voname,
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

    def test_08_config_tomcat_properties(self):
        if osgtest.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return

        server_xml_path = '/etc/tomcat5/server.xml'
        server_xml_backup = server_xml_path + '.osgtest.backup'
        shutil.move(server_xml_path, server_xml_backup)

        source_file = open(server_xml_backup, 'r')
        contents = source_file.read()
        source_file.close()

        new_contents = re.sub(r'crlRequired=".*?"', 'crlRequired="false"',
                              contents, re.IGNORECASE)

        target_file = open(server_xml_path, 'w')
        target_file.write(new_contents)
        target_file.close()

    def test_09_start_voms(self):
        TestVOMS.__started_voms = False
        if not osgtest.rpm_is_installed('voms-server'):
            osgtest.skip('not installed')
            return
        if os.path.exists(TestVOMS.__sentinel_voms):
            osgtest.skip('apparently running')
            return
        command = ('service', 'voms', 'start')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Start VOMS service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(os.path.exists(TestVOMS.__sentinel_voms),
                     'VOMS server PID file is missing')
        TestVOMS.__started_voms = True

    def test_10_record_vomsadmin_start(self):
        TestVOMS.__vomsadmin_log_start = 0
        if osgtest.missing_rpm('tomcat5', 'voms-admin-server'):
            return
        if os.path.exists(TestVOMS.__vomsadmin_logfile):
            TestVOMS.__vomsadmin_log_start = \
                os.path.getsize(TestVOMS.__vomsadmin_logfile)

    def test_11_start_tomcat(self):
        TestVOMS.__started_tomcat = False
        if not osgtest.rpm_is_installed('tomcat5'):
            osgtest.skip('not installed')
            return
        if os.path.exists(TestVOMS.__sentinel_tomcat):
            osgtest.skip('apparently running')
            return
        command = ('service', 'tomcat5', 'start')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Start Tomcat service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(os.path.exists(TestVOMS.__sentinel_tomcat),
                     'Tomcat server PID file is missing')
        TestVOMS.__started_tomcat = True

    def test_12_start_voms_admin(self):
        TestVOMS.__started_voms_admin = False
        if not osgtest.rpm_is_installed('voms-admin-server'):
            osgtest.skip('not installed')
            return
        if os.path.exists(TestVOMS.__sentinel_voms_admin):
            osgtest.skip('apparently running')
            return
        command = ('service', 'voms-admin', 'start')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Start VOMS Admin service', status, stdout,
                                stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(os.path.exists(TestVOMS.__sentinel_voms_admin),
                     'VOMS Admin VO context file is missing')
        TestVOMS.__started_voms_admin = True

    def test_13_wait_for_voms_admin(self):
        if osgtest.missing_rpm('voms-admin-server'):
            return
        line, gap = osgtest.monitor_file(TestVOMS.__vomsadmin_logfile,
                                         TestVOMS.__vomsadmin_log_start,
                                         'VOMS-Admin started succesfully', 60.0)
        self.assert_(line is not None, 'VOMS Admin webapp started')
        osgtest.log_message('VOMS Admin started after %.1f seconds' % gap)

    def test_14_open_access(self):
        if osgtest.missing_rpm('voms-admin-server', 'voms-admin-client'):
            return

        command = ('voms-admin', '--nousercert', '--vo', TestVOMS.__voname,
                   'add-ACL-entry', '/' + TestVOMS.__voname, 'ANYONE',
                   'VOMS_CA', 'CONTAINER_READ,MEMBERSHIP_READ', 'true')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Add VOMS Admin ACL entry', status, stdout,
                                stderr)
        self.assertEqual(status, 0, fail)

    def test_15_advertise(self):
        TestVOMS.__installed_vomses = False
        if osgtest.missing_rpm('voms-admin-server'):
            return

        if os.path.exists('/etc/vomses'):
            shutil.move('/etc/vomses', '/etc/vomses.osg-test.backup')

        vo = TestVOMS.__voname
        hostname = socket.getfqdn()
        host_dn, host_issuer = osgtest.certificate_info(TestVOMS.__hostcert)

        vomses = open('/etc/vomses', 'w')
        vomses.write('"%s" "%s" "%d" "%s" "%s"\n' % \
                     (vo, hostname, 15151, host_dn, vo))
        vomses.close()
        TestVOMS.__installed_vomses = True

        if not os.path.isdir(TestVOMS.__vo_lsc_dir):
            os.mkdir(TestVOMS.__vo_lsc_dir)
        vo_lsc_path = os.path.join(TestVOMS.__vo_lsc_dir, hostname + '.lsc')
        vo_lsc_file = open(vo_lsc_path, 'w')
        vo_lsc_file.write(host_dn + '\n')
        vo_lsc_file.write(host_issuer + '\n')
        vo_lsc_file.close()

        osgtest.syspipe('ls -ldF /etc/*vom*', shell=True)
        osgtest.syspipe(('find', '/etc/grid-security/vomsdir', '-ls'))

    # ==========================================================================

    def test_40_add_user(self):
        if osgtest.missing_rpm('voms-admin-server', 'voms-admin-client'):
            return

        pwd_entry = pwd.getpwnam(osgtest.options.username)
        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_cert_dn, user_cert_issuer = osgtest.certificate_info(cert_path)
        hostname = socket.getfqdn()

        command = ('voms-admin', '--vo', TestVOMS.__voname, '--host', hostname,
                   '--nousercert', 'create-user', user_cert_dn,
                   user_cert_issuer, 'OSG Test User', 'root@localhost')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Add VO user', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    def test_42_voms_proxy_init(self):
        TestVOMS.__got_proxy = False
        if osgtest.missing_rpm('voms-server', 'voms-clients'):
            return

        command = ('voms-proxy-init', '-voms', TestVOMS.__voname)
        password = osgtest.options.password + '\n'
        status, stdout, stderr = osgtest.syspipe(command, True, password)
        fail = osgtest.diagnose('Run voms-proxy-init', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        TestVOMS.__got_proxy = True

    def test_43_voms_proxy_info(self):
        if osgtest.missing_rpm('voms-clients'):
            return
        if not TestVOMS.__got_proxy:
            osgtest.skip('no proxy')
            return

        command = ('voms-proxy-info', '-all')
        status, stdout, stderr = osgtest.syspipe(command, True)
        fail = osgtest.diagnose('Run voms-proxy-info', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(('/%s/Role=NULL' % (TestVOMS.__voname)) in stdout,
                     'voms-proxy-info output contains sentinel')

    def test_44_voms_proxy_init(self):
        if osgtest.missing_rpm('voms-server', 'voms-clients'):
            return

        command = ('voms-proxy-init', '-voms', TestVOMS.__voname + ':/Bogus')
        password = osgtest.options.password + '\n'
        status, stdout, stderr = osgtest.syspipe(command, True, password)
        self.assertNotEqual(status, 0, 'voms-proxy-init fails on bad group')
        self.assert_('Unable to satisfy' in stdout,
                     'voms-proxy-init failure message')

    # Copy of 43 above, to make sure failure did not affect good proxy
    def test_45_voms_proxy_info(self):
        if osgtest.missing_rpm('voms-clients'):
            return
        if not TestVOMS.__got_proxy:
            osgtest.skip('no proxy')
            return

        command = ('voms-proxy-info', '-all')
        status, stdout, stderr = osgtest.syspipe(command, True)
        fail = osgtest.diagnose('Run voms-proxy-info', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(('/%s/Role=NULL' % (TestVOMS.__voname)) in stdout,
                     'voms-proxy-info output extended attribute')

    # ==========================================================================

    def test_50_config_mkgridmap(self):
        if osgtest.missing_rpm('edg-mkgridmap'):
            return
        contents = 'group vomss://%s:8443/voms/%s %s\n' % \
            (socket.getfqdn(), TestVOMS.__voname, osgtest.options.username)
        config = open(TestVOMS.__mkgridmap_conf, 'w')
        config.write(contents)
        config.close()
        osgtest.syspipe(('cat', TestVOMS.__mkgridmap_conf))

    def test_51_edg_mkgridmap(self):
        if osgtest.missing_rpm('edg-mkgridmap'):
            return
        command = ('edg-mkgridmap', '--conf', TestVOMS.__mkgridmap_conf)
        os.environ['GRIDMAP'] = '/usr/share/osg-test/grid-mapfile'
        os.environ['USER_VO_MAP'] = '/usr/share/osg-test/user-vo-map'
        os.environ['EDG_MKGRIDMAP_LOG'] = \
            '/usr/share/osg-test/edg-mkgridmap.log'
        os.environ['VO_LIST_FILE'] = '/usr/share/osg-test/vo-list-file'
        os.environ['UNDEFINED_ACCTS_FILE'] = '/usr/share/osg-test/undef-ids'
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Run edg-mkgridmap', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

        pwd_entry = pwd.getpwnam(osgtest.options.username)
        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_cert_dn, user_cert_issuer = osgtest.certificate_info(cert_path)
        expected = '"%s" %s' % (user_cert_dn, osgtest.options.username)
        gridmap_file = open(os.environ['GRIDMAP'], 'r')
        contents = gridmap_file.read()
        gridmap_file.close()
        self.assert_(expected in contents, 'Expected grid-mapfile contents')

    # ==========================================================================

    def test_90_clean_edg_mkgridmap(self):
        if osgtest.missing_rpm('edg-mkgridmap'):
            return

        for envvar in ('VO_LIST_FILE', 'UNDEFINED_ACCTS_FILE',
                       'EDG_MKGRIDMAP_LOG', 'USER_VO_MAP', 'GRIDMAP'):
            if os.path.exists(os.environ[envvar]):
                os.remove(os.environ[envvar])
            del os.environ[envvar]
        if os.path.exists(TestVOMS.__mkgridmap_conf):
            os.remove(TestVOMS.__mkgridmap_conf)

    def test_91_restore_vomses(self):
        if os.path.isdir(TestVOMS.__vo_lsc_dir):
            shutil.rmtree(TestVOMS.__vo_lsc_dir)
        if TestVOMS.__installed_vomses:
            os.remove('/etc/vomses')
        if os.path.exists('/etc/vomses.osg-test.backup'):
            shutil.move('/etc/vomses.osg-test.backup', '/etc/vomses')

    def test_92_stop_voms_admin(self):
        if not osgtest.rpm_is_installed('voms-admin-server'):
            osgtest.skip('not installed')
            return
        if TestVOMS.__started_voms_admin == False:
            osgtest.skip('did not start webapp')
            return

        command = ('service', 'voms-admin', 'stop')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Stop VOMS Admin service', status, stdout,
                                stderr)
        self.assertEqual(status, 0, fail)
        # self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(not os.path.exists(TestVOMS.__sentinel_voms_admin),
                     'VOMS Admin VO context file still exists')

    def test_93_stop_tomcat(self):
        if not osgtest.rpm_is_installed('tomcat5'):
            osgtest.skip('not installed')
            return
        if TestVOMS.__started_tomcat == False:
            osgtest.skip('did not start server')
            return

        command = ('service', 'tomcat5', 'stop')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Stop Tomcat service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(not os.path.exists(TestVOMS.__sentinel_tomcat),
                     'Tomcat server PID file still exists')

    def test_94_stop_voms(self):
        if not osgtest.rpm_is_installed('voms-server'):
            osgtest.skip('not installed')
            return
        if TestVOMS.__started_voms == False:
            osgtest.skip('did not start server')
            return

        command = ('service', 'voms', 'stop')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Stop VOMS service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(not os.path.exists(TestVOMS.__sentinel_voms),
                     'VOMS server PID file still exists')

    def test_95_deconfig_tomcat_properties(self):
        if osgtest.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return
        server_xml_path = '/etc/tomcat5/server.xml'
        server_xml_backup = server_xml_path + '.osgtest.backup'
        shutil.move(server_xml_backup, server_xml_path)

    def test_96_remove_trustmanager(self):
        if osgtest.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return

        # mv -f /etc/tomcat5/server.xml.old-trustmanager /etc/tomcat5/server.xml
        old_tm = '/etc/tomcat5/server.xml.old-trustmanager'
        new_tm = '/etc/tomcat5/server.xml'
        if os.path.exists(old_tm) and os.path.isdir(os.path.dirname(new_tm)):
            shutil.move(old_tm, new_tm)

        # rm -f /usr/share/tomcat5/server/lib/bcprov*.jar
        for jar in glob.glob('/usr/share/tomcat5/server/lib/bcprov*.jar'):
            os.remove(jar)

        # rm -f /usr/share/tomcat5/server/lib/log4j*.jar
        for jar in glob.glob('/usr/share/tomcat5/server/lib/log4j*.jar'):
            os.remove(jar)

        # rm -f /usr/share/tomcat5/server/lib/trustmanager-*.jar
        for j in glob.glob('/usr/share/tomcat5/server/lib/trustmanager-*.jar'):
            os.remove(j)

        # rm -f /etc/tomcat5/log4j-trustmanager.properties
        if os.path.exists('/etc/tomcat5/log4j-trustmanager.properties'):
            os.remove('/etc/tomcat5/log4j-trustmanager.properties')

        # rm -f /var/lib/trustmanager-tomcat/server.xml
        if os.path.exists('/var/lib/trustmanager-tomcat/server.xml'):
            os.remove('/var/lib/trustmanager-tomcat/server.xml')

        osgtest.log_message('EMI trustmanager removed')

    def test_97_remove_vo(self):
        if osgtest.missing_rpm('voms-admin-server', 'voms-mysql-plugin'):
            return

        # Configure VOMS Admin with new VO
        db_user_name = 'admin-' + TestVOMS.__voname
        command = ('voms-admin-configure', 'remove', '--vo', TestVOMS.__voname,
                   '--undeploy-database')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Remove VO', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_('Database undeployed correctly!' in stdout, fail)
        self.assert_(' succesfully removed.' in stdout, fail)

        # Really remove database
        mysql_statement = "DROP DATABASE `voms_%s`" % (TestVOMS.__voname)
        command = ('mysql', '-u', 'root', '-e', mysql_statement)
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Drop MYSQL VOMS database',
                                status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    # Do the keys first, so that the directories will be empty for the certs.
    def test_98_remove_certs(self):
        self.remove_cert('vomskey')
        self.remove_cert('vomscert')
        self.remove_cert('httpkey')
        self.remove_cert('httpcert')

    def test_99_stop_mysqld(self):
        if not osgtest.rpm_is_installed('mysql-server'):
            osgtest.skip('not installed')
            return
        if TestVOMS.__started_mysqld == False:
            osgtest.skip('did not start server')
            return

        command = ('service', 'mysqld', 'stop')
        status, stdout, stderr = osgtest.syspipe(command)
        fail = osgtest.diagnose('Stop MySQL service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(not os.path.exists(TestVOMS.__sentinel_mysqld),
                     'MySQL server PID file still exists')
