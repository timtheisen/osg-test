import os
import os.path
import osgtest
import pwd
import re
import shutil
import unittest

class TestCleanup(unittest.TestCase):

    def test_01_remove_test_user(self):
        if (osgtest.mapfile is not None) and os.path.exists(osgtest.mapfile):
            os.remove(osgtest.mapfile)
        backup = osgtest.mapfile_backup
        if (backup is not None) and os.path.exists(backup):
            shutil.move(backup, '/etc/grid-security/grid-mapfile')

        password_entry = pwd.getpwnam(osgtest.options.username)

        globus_dir = os.path.join(password_entry.pw_dir, '.globus')

        usercert_path = os.path.join(globus_dir, 'usercert.pem')
        if os.path.exists(usercert_path):
            os.unlink(usercert_path)

        userkey_path = os.path.join(globus_dir, 'userkey.pem')
        if os.path.exists(userkey_path):
            os.unlink(userkey_path)

        mail_path = os.path.join('/var/spool/mail', osgtest.options.username)
        if os.path.exists(mail_path):
            os.unlink(mail_path)

        if os.path.isdir(password_entry.pw_dir):
            shutil.rmtree(password_entry.pw_dir)

        command = ('userdel', osgtest.options.username)
        status, stdout, stderr = osgtest.syspipe(command)
        self.assertEqual(status, 0,
                         "Removing user '%s' failed with exit status %d" %
                         (osgtest.options.username, status))

    def test_02_remove_packages(self):
        if len(osgtest.original_rpms) == 0:
            osgtest.skip('no original list')
            return
        current_rpms = osgtest.installed_rpms()
        new_rpms_since_install = current_rpms - osgtest.original_rpms
        if len(new_rpms_since_install) == 0:
            osgtest.skip('no new RPMs')
            return

        # For the "rpm -e" command, RPMs should be listed in the same order as
        # installed.  Why?  The erase command processes files in reverse order
        # as listed on the command line, mostly; it seems to do a bit of
        # reordering (search -vv output for "tsort"), but it is not clear what
        # the algorithm is.  So, rpm will cheerfully erase a package, the
        # contents of which are needed by the pre- or post-uninstall scriptlets
        # of a package that will be erased later in sequence.  By listing them
        # in yum install order, we presumably get a valid ordering and increase
        # the chances of a clean erase.

        rpm_erase_candidates = []
        for package in osgtest.installed_rpm_list:
            if package in new_rpms_since_install:
                rpm_erase_candidates.append(package)

        remaining_new_rpms = new_rpms_since_install - set(rpm_erase_candidates)
        if len(remaining_new_rpms) > 0:
            osgtest.log_message('%d RPMs installed but not in yum output' % \
                                (len(remaining_new_rpms)))
            rpm_erase_candidates += remaining_new_rpms

        # Creating the list of RPMs to erase is more complicated than just using
        # the list of new RPMs, because there may be RPMs with both 32- and
        # 64-bit versions installed.  In that case, rpm will fail if given just
        # the base package name; instead, the architecture must be specified,
        # and an easy way to get that information is from 'rpm -q'.  So we use
        # the bare name when possible, and the fully versioned one when
        # necessary.

        rpm_erase_list = []
        for package in rpm_erase_candidates:
            command = ('rpm', '--query', package)
            status, stdout, stderr = osgtest.syspipe(command, log_output=False)
            versioned_rpms = re.split('\n', stdout.strip())
            if len(versioned_rpms) > 1:
                rpm_erase_list += versioned_rpms
            else:
                rpm_erase_list.append(package)

        command = ['rpm', '--quiet', '--erase'] + rpm_erase_list
        status, stdout, stderr = osgtest.syspipe(command)
        self.assertEqual(status, 0,
                         "Removing %d packages failed with exit status %d" %
                         (len(rpm_erase_list), status))
