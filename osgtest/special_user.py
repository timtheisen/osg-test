import os
import os.path
import osgtest
import pwd
import re
import shutil
import unittest

class TestUser(unittest.TestCase):

    def test_01_add_user(self):
        # Bail out if this step is not needed
        if not osgtest.options.adduser:
            osgtest.skip('not requested')
            return
        try:
            pwd.getpwnam(osgtest.options.username)
        except KeyError:
            pass # expected
        else:
            osgtest.skip('user exists')
            return

        # Add
        if not os.path.isdir(osgtest.HOME_DIR):
            os.mkdir(osgtest.HOME_DIR)
        command = ['useradd',
                   '--base-dir', osgtest.HOME_DIR, '-n',
                   '--shell', '/bin/sh',
                   osgtest.options.username]
        (status, stdout, stderr) = osgtest.syspipe(command)
        self.assertEqual(status, 0,
                         "Adding user '%s' failed with exit status %d"
                         % (osgtest.options.username, status))

        # Set up certificate
        password_entry = pwd.getpwnam(osgtest.options.username)
        globus_dir = os.path.join(password_entry[5], '.globus')
        if not os.path.isdir(globus_dir):
            os.mkdir(globus_dir)
        shutil.copy2('/usr/share/osg-test/usercert.pem', globus_dir)
        shutil.copy2('/usr/share/osg-test/userkey.pem', globus_dir)
        os.chmod(os.path.join(globus_dir, 'usercert.pem'), 0644)
        os.chmod(os.path.join(globus_dir, 'userkey.pem'), 0400)
        os.chown(os.path.join(globus_dir, 'usercert.pem'),
                 password_entry[2], password_entry[3])
        os.chown(os.path.join(globus_dir, 'userkey.pem'),
                 password_entry[2], password_entry[3])

    def test_02_user(self):
        password_entry = pwd.getpwnam(osgtest.options.username)
        self.assert_(password_entry is not None,
                     "The user '%s' does not exist" % osgtest.options.username)
        self.assert_(os.path.isdir(password_entry[5]),
                     "The user '%s' does not have a home directory at '%s'" %
                     (osgtest.options.username, password_entry[5]))

    def test_03_install_mapfile(self):
        try:
            password_entry = pwd.getpwnam(osgtest.options.username)
        except KeyError, e:
            osgtest.skip('no user')
            return

        backup_filename = '/etc/grid-security/grid-mapfile.osg-test.backup'
        if os.path.exists('/etc/grid-security/grid-mapfile'):
            shutil.move('/etc/grid-security/grid-mapfile', backup_filename)
            osgtest.mapfile_backup = backup_filename

        cert_path = os.path.join(password_entry[5], '.globus', 'usercert.pem')
        command = ['openssl', 'x509', '-in', cert_path, '-noout', '-subject']
        (status, stdout, stderr) = osgtest.syspipe(command)
        self.assertEqual(status, 0, 'Could not read user certificate')
        user_dn = re.sub(r'^[^/]*', '', stdout.strip())

        mapfile = open('/etc/grid-security/grid-mapfile', 'w')
        mapfile.write('"%s" %s\n' % (user_dn, password_entry[0]))
        mapfile.close()
        osgtest.mapfile = '/etc/grid-security/grid-mapfile'
