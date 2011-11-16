import os
import osgtest
import pwd
import shutil
import unittest

class TestVOMS(unittest.TestCase):

    # "Constants"
    __sentinel_mysqld = '/var/run/mysqld/mysqld.pid'
    __hostcert = '/etc/grid-security/hostcert.pem'
    __hostkey = '/etc/grid-security/hostkey.pem'

    # Certificate stuff
    __certs = {}
    __certs['vomscert'] = '/etc/grid-security/voms/vomscert.pem'
    __certs['vomskey'] = '/etc/grid-security/voms/vomskey.pem'
    __certs['httpcert'] = '/etc/grid-security/http/httpcert.pem'
    __certs['httpkey'] = '/etc/grid-security/http/httpkey.pem'

    # Class attributes
    __started_mysqld = False
    __installed_vomscert = False

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
            print "********** GOT HERE **********"
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
        command = ['service', 'mysqld', 'start']
        (status, stdout, stderr) = osgtest.syspipe(command)
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

    def test_50_placeholder(self):
        osgtest.log_message('VOMS tests happen here')

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

        command = ['service', 'mysqld', 'stop']
        (status, stdout, stderr) = osgtest.syspipe(command)
        fail = osgtest.diagnose('Stop MySQL service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(not os.path.exists(TestVOMS.__sentinel_mysqld),
                     'MySQL server PID file still exists')
