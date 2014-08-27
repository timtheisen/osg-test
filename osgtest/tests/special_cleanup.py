import subprocess
import signal
import os
import os.path
import pwd
import re
import shutil
import time

import osgtest.library.core as core
import osgtest.library.yum as yum
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.certificates as certs

class TestCleanup(osgunittest.OSGTestCase):

    # Never declare a skipped test in this module.  The intent of an "ok skip"
    # is to note a test that could have run, had other packages been installed.
    # But in this module, functions are skipped due to other runtime conditions,
    # so the correct behavior is to log a message and return.

    def list_special_install_rpms(self, rpm_list):
        # For the "rpm -e" command, RPMs should be listed in the same order as
        # installed.  Why?  The erase command processes files in reverse order
        # as listed on the command line, mostly; it seems to do a bit of
        # reordering (search -vv output for "tsort"), but it is not clear what
        # the algorithm is.  So, rpm will cheerfully erase a package, the
        # contents of which are needed by the pre- or post-uninstall scriptlets
        # of a package that will be erased later in sequence.  By listing them
        # in yum install order, we presumably get a valid ordering and increase
        # the chances of a clean erase.
        
        rpm_candidates = []
        for package in rpm_list:
            status, stdout, _ = core.system(('rpm', '--query', package, '--queryformat', r'%{NAME}'))
            if status == 0 and stdout in rpm_list:
                rpm_candidates.append(stdout)
        remaining_rpms = set(rpm_list) - set(rpm_candidates)
        count = len(remaining_rpms)
        if count > 0:
            core.log_message('%d RPMs installed but not in yum output' % count)
            rpm_candidates += remaining_rpms

        # Creating the list of RPMs to erase/downgrade is more complicated than just using
        # the list of new RPMs, because there may be RPMs with both 32- and
        # 64-bit versions installed.  In that case, rpm will fail if given just
        # the base package name; instead, the architecture must be specified,
        # and an easy way to get that information is from 'rpm -q'.  So we use
        # the bare name when possible, and the fully versioned one when
        # necessary.
            
        final_rpm_list = []
        for package in rpm_candidates:
            command = ('rpm', '--query', package, '--queryformat',
                       r'%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n')
            status, stdout, _  = core.system(command, log_output=False)
            versioned_rpms = re.split('\n', stdout.strip())
            if len(versioned_rpms) > 1:
                final_rpm_list += versioned_rpms
            else:
                final_rpm_list.append(package)

        return final_rpm_list

    def test_01_downgrade_osg_release(self):
        if not (core.options.updaterelease):
            return

        self.skip_ok_unless(core.state['install.release-updated'], 'release not updated')

        command = ['rpm', '-e', 'osg-release']
        core.check_system(command, 'Erase osg-release')
        
        rpm_url = 'http://repo.grid.iu.edu/osg/' + core.config['install.original-release-ver']+ '/osg-' + \
            core.config['install.original-release-ver'] + '-el' + str(core.el_release()) + '-release-latest.rpm'
        command = ['rpm', '-Uvh', rpm_url]
        core.check_system(command, 'Downgrade osg-release')

    def test_02_downgrade_xrootd4(self):
        # If we replaced xrootd-* with xrootd4* on EL5, we need to handle downgrades gracefully
        # Otherwise, we can skip this and downgrade as we normally do
        if core.el_release() > 5:
            return
        self.skip_ok_unless(core.state['install.xrootd-replaced'], 'xrootd-* was not replaced')

        # This also removes any package that required xrootd4*! If we're not
        # supposed to be removing these packages, they will be orphaned and
        # and reinstalled in test_04_orphaned_packages
        deadline = time.time() + 3600
        command = ['yum', '-y', 'remove', 'xrootd4*']
        fail_msg, status, stdout, stderr = yum.retry_command(command, deadline)
        if fail_msg:
            self.fail(fail_msg)
        yum.parse_output_for_packages(stdout)

    def test_03_remove_packages(self):
        # We didn't ask to install anything
        if len(core.options.packages) == 0:
            return

        # Nothing actually got installed
        if len(core.state['install.installed']) == 0:
            core.log_message('No packages installed')
            return

        deadline = time.time() + 3600
        el_version = core.el_release()

        if el_version == 6:
            # Rolling back is a lot more reliable in yum post EL5
            core.state['install.transaction_ids'].reverse()
            for transaction in core.state['install.transaction_ids']:
                command = ('yum', 'history', 'undo', '-y', transaction)
                fail_msg, status, stdout, stderr = yum.retry_command(command, deadline)
                if fail_msg:
                    self.fail(fail_msg)
        elif el_version == 5:
            # rpm -Uvh --rollback was very finicky so we had to
            # spin up our own method of rolling back installations
            if len(core.state['install.updated']) != 0:
                rpm_downgrade_list = self.list_special_install_rpms(core.state['install.updated'])
                package_count = len(rpm_downgrade_list)
                command = ['yum', '-y', 'downgrade'] + rpm_downgrade_list
                fail_msg, status, stdout, stderr = yum.retry_command(command, deadline)
                if fail_msg:
                    self.fail(fail_msg)
                yum.parse_output_for_packages(stdout)
                
            if len(core.state['install.installed']) != 0:
                rpm_erase_list = self.list_special_install_rpms(core.state['install.installed'])
                package_count = len(rpm_erase_list)
                command = ['rpm', '--quiet', '--erase'] + rpm_erase_list
                core.check_system(command, 'Remove %d packages' % (package_count))
            else:
                core.log_message('No new RPMs')
                return

    def test_04_restore_orphaned_packages(self):
        if core.state['install.orphaned']:
            self.skip_ok_unless(core.state['install.orphaned'], 'No orphaned packages')
            # Reinstall packages that we removed but didn't install
            # Technically, this doesn't bring the system back to its original
            # state of packages: we don't track state of EPEL/OSG repos and we
            # leave the ones we drop in
            deadline = time.time() + 3600
            command = ['yum', '-y', 'install'] + core.state['install.orphaned']
            fail_msg, status, stdout, stderr = yum.retry_command(command, deadline)
            if fail_msg:
                self.fail(fail_msg)

    def test_05_restore_mapfile(self):
        if core.state['system.wrote_mapfile']:
            files.restore(core.config['system.mapfile'], 'user')


    def test_06_cleanup_test_certs(self):
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

    def test_07_remove_test_user(self):
        if not core.state['general.user_added']:
            core.log_message('Did not add user')
            return

        username = core.options.username
        password_entry = pwd.getpwnam(username)
        globus_dir = os.path.join(password_entry.pw_dir, '.globus')

        # Remove certs in case userdel fails
        files.remove(os.path.join(globus_dir, 'usercert.pem'))
        files.remove(os.path.join(globus_dir, 'userkey.pem'))

        # Get list of PIDs owned by the test user
        command = ('ps', '-U', username, '-u', username, '-o', 'pid=')
        _, output, _ = core.system(command)

        # Take no prisoners 
        for pid in output.splitlines():
            try:
                os.kill(int(pid), signal.SIGKILL)
            except OSError:
                continue

        command = ('userdel', username)
        core.check_system(command, "Remove user '%s'" % (username))

        files.remove(os.path.join('/var/spool/mail', username))
        shutil.rmtree(password_entry.pw_dir)

    def test_08_enable_osg_release(self):
        # Re-enable osg-release on EL7 (to mirror the disabling in special_cleanup) 
        # This can be removed when we release something on EL7
        self.skip_ok_unless(core.el_release() == 7, 'Non-EL7 release')
        files.restore(core.config['install.osg-repo-path'], owner='install')

    # The backups test should always be last, in case any prior tests restore
    # files from backup.
    def test_09_backups(self):
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
