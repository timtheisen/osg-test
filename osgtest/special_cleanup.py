import os
import os.path
import osgtest
import pwd
import shutil
import unittest

class TestCleanup(unittest.TestCase):

    def test_01_remove_test_user(self):
        password_entry = pwd.getpwnam(osgtest.options.username)

        globus_dir = os.path.join(password_entry[5], '.globus')

        usercert_path = os.path.join(globus_dir, 'usercert.pem')
        if os.path.exists(usercert_path):
            os.unlink(usercert_path)

        userkey_path = os.path.join(globus_dir, 'userkey.pem')
        if os.path.exists(userkey_path):
            os.unlink(userkey_path)

        mail_path = os.path.join('/var/spool/mail', osgtest.options.username)
        if os.path.exists(mail_path):
            os.unlink(mail_path)

        if os.path.isdir(password_entry[5]):
            shutil.rmtree(password_entry[5])

        command = ['userdel', osgtest.options.username]
        (status, stdout, stderr) = osgtest.syspipe(command)
        self.assertEqual(status, 0,
                         "Removing user '%s' failed with exit status %d" %
                         (osgtest.options.username, status))

    def test_02_remove_packages(self):
        if len(osgtest.original_rpms) == 0:
            osgtest.skip('no original list')
            return
        current_rpms = osgtest.installed_rpms()
        rpms_to_erase = current_rpms - osgtest.original_rpms
        if len(rpms_to_erase) == 0:
            osgtest.skip('no new RPMs')
            return
        command = ['rpm', '--quiet', '--erase'] + list(rpms_to_erase)
        (status, stdout, stderr) = osgtest.syspipe(command)
        self.assertEqual(status, 0,
                         "Removing %d packages failed with exit status %d" %
                         (len(rpms_to_erase), status))
