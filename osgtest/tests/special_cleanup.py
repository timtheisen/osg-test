import os
import os.path
import pwd
import re
import shutil
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.certificates as certs

class TestCleanup(osgunittest.OSGTestCase):

    # Never declare a skipped test in this module.  The intent of an "ok skip"
    # is to note a test that could have run, had other packages been installed.
    # But in this module, functions are skipped due to other runtime conditions,
    # so the correct behavior is to log a message and return.

    def test_01_remove_packages(self):
        if ('install.preinstalled' not in core.state) or (len(core.state['install.preinstalled']) == 0):
            core.log_message('No original list')
            return
        if 'install.installed' not in core.state:
            core.log_message('No packages installed')
            return

        current_rpms = core.installed_rpms()
        new_rpms = current_rpms - core.state['install.preinstalled']
        if len(new_rpms) == 0:
            core.log_message('No new RPMs')
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
        if core.options.updaterepo:
            special_install_rpms = core.state['install.installed'] + core.state['install.updated']
        else:
            special_install_rpms = core.state['install.installed']
        for package in special_install_rpms:
            status, stdout, stderr = core.system(('rpm', '--query', package, '--queryformat', r'%{NAME}'))
            if status == 0 and stdout in new_rpms:
                rpm_erase_candidates.append(stdout)
        remaining_new_rpms = new_rpms - set(rpm_erase_candidates)
        count = len(remaining_new_rpms)
        if count > 0:
            core.log_message('%d RPMs installed but not in yum output' % count)
            rpm_erase_candidates += remaining_new_rpms

        # Samba dependencies break cleanup on fermicloud SL6 VM's (SOFTWARE-1140)
        if 'samba-winbind' in rpm_erase_candidates:
            rpm_erase_candidates.remove('samba-winbind')
            
        # Creating the list of RPMs to erase is more complicated than just using
        # the list of new RPMs, because there may be RPMs with both 32- and
        # 64-bit versions installed.  In that case, rpm will fail if given just
        # the base package name; instead, the architecture must be specified,
        # and an easy way to get that information is from 'rpm -q'.  So we use
        # the bare name when possible, and the fully versioned one when
        # necessary.

        rpm_erase_list = []
        for package in rpm_erase_candidates:
            command = ('rpm', '--query', package, '--queryformat',
                       r'%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n')
            status, stdout, stderr = core.system(command, log_output=False)
            versioned_rpms = re.split('\n', stdout.strip())
            if len(versioned_rpms) > 1:
                rpm_erase_list += versioned_rpms
            else:
                rpm_erase_list.append(package)

        package_count = len(rpm_erase_list)
        command = ['rpm', '--quiet', '--erase'] + rpm_erase_list
        core.check_system(command, 'Remove %d packages' % (package_count))


    def test_02_restore_mapfile(self):
        if core.state['system.wrote_mapfile']:
            files.restore(core.config['system.mapfile'], 'user')


    def test_03_cleanup_test_certs(self):
        if core.state['certs.dir_created']:
            files.remove('/etc/grid-security/certificates', force=True)
        else:
            files.remove('/etc/grid-security/certificates/' + core.config['certs.test-ca-hash'] + '*')
            try:
                files.remove('/etc/grid-security/certificates/' + core.config['certs.test-ca-hash-old'] + '.*')
            except KeyError:
                pass
            files.remove('/etc/grid-security/certificates/OSG-Test-CA.*')

        if core.state['certs.hostcert_created']:
            files.remove(core.config['certs.hostcert'])
            files.remove(core.config['certs.hostkey'])
            
        certs.cleanup_files()

    def test_04_remove_test_user(self):
        if not core.state['general.user_added']:
            core.log_message('Did not add user')
            return

        username = core.options.username
        password_entry = pwd.getpwnam(username)
        globus_dir = os.path.join(password_entry.pw_dir, '.globus')

        command = ('userdel', username)
        core.check_system(command, "Remove user '%s'" % (username))

        files.remove(os.path.join(globus_dir, 'usercert.pem'))
        files.remove(os.path.join(globus_dir, 'userkey.pem'))
        files.remove(os.path.join('/var/spool/mail', username))
        shutil.rmtree(password_entry.pw_dir)


    # The backups test should always be last, in case any prior tests restore
    # files from backup.
    def test_05_backups(self):
        record_is_clear = True
        if len(files._backups) > 0:
            details = ''
            for id, backup_path in files._backups.items():
                details += "-- Backup of '%s' for '%s' in '%s'\n" % (id[0], id[1], backup_path)
            core.log_message('Backups remain in backup dictionary:\n' + details)
            record_is_clear = False

        actual_is_clear = True
        if os.path.isdir(files._backup_directory):
            backups = os.listdir(files._backup_directory)
            if len(backups) > 0:
                core.log_message("Files remain in '%s:'" % (files._backup_directory))
                core.system('ls -lF ' + files._backup_directory, shell=True)
                actual_is_clear = False
            shutil.rmtree(files._backup_directory, ignore_errors=True)

        self.assert_(record_is_clear and actual_is_clear, 'Backups were not restored fully')
