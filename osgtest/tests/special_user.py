import os
import os.path
import osgtest.library.core as core
import osgtest.library.files as files
import pwd
import shutil
import unittest

class TestUser(unittest.TestCase):

    def test_01_add_user(self):
        core.state['general.user_added'] = False

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
        home_dir = core.config['user.home']
        if not os.path.isdir(home_dir):
            os.mkdir(home_dir)
        command = ('useradd', '--base-dir', home_dir, '-n', '--shell', '/bin/sh', core.options.username)
        core.check_system(command, 'Add user %s' % (core.options.username))
        core.state['general.user_added'] = True

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
        os.chown(os.path.join(globus_dir, 'usercert.pem'), user.pw_uid, user.pw_gid)
        os.chown(os.path.join(globus_dir, 'userkey.pem'), user.pw_uid, user.pw_gid)

    def test_02_user(self):
        if not (core.options.runtests or core.options.adduser):
            core.skip('no user needed')
            return
        try:
            password_entry = pwd.getpwnam(core.options.username)
        except KeyError, e:
            self.fail("User '%s' should exist but does not" % core.options.username)
        self.assert_(password_entry.pw_dir != '/', "User '%s' has home directory at '/'" % (core.options.username))
        self.assert_(os.path.isdir(password_entry.pw_dir),
                     "User '%s' missing a home directory at '%s'" % (core.options.username, password_entry.pw_dir))

    def test_03_install_mapfile(self):
        try:
            pwd_entry = pwd.getpwnam(core.options.username)
        except KeyError:
            core.skip('no user')
            return
        if pwd_entry.pw_dir == '/':
            core.skip('no user home dir')
            return
        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_dn, user_cert_issuer = core.certificate_info(cert_path)
        files.append(core.config['system.mapfile'], '"%s" %s\n' % (user_dn, pwd_entry.pw_name), owner='user')
        os.chmod(core.config['system.mapfile'], 0644)
