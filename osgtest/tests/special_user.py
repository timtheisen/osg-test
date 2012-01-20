import os
import os.path
import osgtest.library.core as core
import pwd
import re
import shutil
import unittest

class TestUser(unittest.TestCase):

    def test_01_add_user(self):
        # Bail out if this step is not needed
        if not core.options.adduser:
            core.skip('not requested')
            return
        try:
            pwd.getpwnam(core.options.username)
        except KeyError:
            pass # expected
        else:
            core.skip('user exists')
            return

        # Add
        if not os.path.isdir(core.HOME_DIR):
            os.mkdir(core.HOME_DIR)
        command = ('useradd', '--base-dir', core.HOME_DIR, '-n',
                   '--shell', '/bin/sh', core.options.username)
        status, stdout, stderr = core.syspipe(command)
        self.assertEqual(status, 0,
                         "Adding user '%s' failed with exit status %d"
                         % (core.options.username, status))

        # Set up directories
        user = pwd.getpwnam(core.options.username)
        os.chown(user.pw_dir, user.pw_uid, user.pw_gid)
        os.chmod(user.pw_dir, 0755)
        globus_dir = os.path.join(user.pw_dir, '.globus')
        if not os.path.isdir(globus_dir):
            os.mkdir(globus_dir)
            os.chown(globus_dir, user.pw_uid, user.pw_gid)
            os.chmod(globus_dir, 0755)

        # Set up certificate
        shutil.copy2('/usr/share/osg-test/usercert.pem', globus_dir)
        shutil.copy2('/usr/share/osg-test/userkey.pem', globus_dir)
        os.chmod(os.path.join(globus_dir, 'usercert.pem'), 0644)
        os.chmod(os.path.join(globus_dir, 'userkey.pem'), 0400)
        os.chown(os.path.join(globus_dir, 'usercert.pem'),
                 user.pw_uid, user.pw_gid)
        os.chown(os.path.join(globus_dir, 'userkey.pem'),
                 user.pw_uid, user.pw_gid)

    def test_02_user(self):
        password_entry = pwd.getpwnam(core.options.username)
        self.assert_(password_entry is not None,
                     "The user '%s' does not exist" % core.options.username)
        self.assert_(os.path.isdir(password_entry.pw_dir),
                     "The user '%s' does not have a home directory at '%s'" %
                     (core.options.username, password_entry.pw_dir))

    def test_03_install_mapfile(self):
        pwd_entry = pwd.getpwnam(core.options.username)
        backup_filename = '/etc/grid-security/grid-mapfile.osg-test.backup'
        if os.path.exists('/etc/grid-security/grid-mapfile'):
            shutil.move('/etc/grid-security/grid-mapfile', backup_filename)
            core.mapfile_backup = backup_filename

        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_dn, user_cert_issuer = core.certificate_info(cert_path)

        mapfile = open('/etc/grid-security/grid-mapfile', 'w')
        mapfile.write('"%s" %s\n' % (user_dn, pwd_entry.pw_name))
        mapfile.close()
        core.mapfile = '/etc/grid-security/grid-mapfile'
