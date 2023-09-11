import errno
import signal
import os
import pwd
import re
import shutil

import osgtest.library.core as core
import osgtest.library.yum as yum
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

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

        # Creating the list of RPMs to erase is more complicated than just using
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
            status, stdout, _ = core.system(command, log_output=False)
            versioned_rpms = re.split('\n', stdout.strip())
            if len(versioned_rpms) > 1:
                final_rpm_list += versioned_rpms
            else:
                final_rpm_list.append(package)

        return final_rpm_list

    def test_01_downgrade_osg_release(self):
        if not core.options.updaterelease:
            return

        self.skip_bad_unless(core.state['install.release-updated'], 'release not updated')

        command = ['rpm', '-e', '--nodeps', 'osg-release']
        core.check_system(command, 'Erase osg-release')

        rpm_url = 'https://repo.opensciencegrid.org/osg/' \
            + core.config['install.original-release-ver'] \
            + '/osg-' \
            + core.config['install.original-release-ver'] \
            + '-el' \
            + str(core.el_release()) \
            + '-release-latest.rpm'
        command = ['yum', 'install', '-y', rpm_url]
        core.check_system(command, 'Downgrade osg-release')

        yum.clean(*core.config['yum.clean_repos'])

    def test_02_remove_packages(self):
        # We didn't ask to install anything
        if len(core.options.packages) == 0:
            return

        # Nothing actually got installed
        if len(core.state['install.installed']) == 0:
            core.log_message('No packages installed')
            return

        for transaction in reversed(sorted(core.state['install.transaction_ids'])):
            command = ['yum', 'history', 'undo', '-y', str(transaction)]
            for repo in core.options.extrarepos:
                command.append('--enablerepo=%s' % repo)
            fail_msg, _, _, _ = yum.retry_command(command)
            if fail_msg:
                self.fail(fail_msg)

    def test_03_selinux(self):
        if not core.options.selinux:
            return

        self.skip_bad_unless(core.rpm_is_installed('libselinux-utils'), 'missing SELinux utils')
        if core.state['selinux.mode'] == 'permissive':
            core.check_system(('setenforce', 'Permissive'), 'set selinux mode to permissive')

    def test_04_restore_orphaned_packages(self):
        # We didn't ask to install anything and thus didn't remove anything
        if len(core.options.packages) == 0:
            return

        if core.state['install.orphaned']:
            self.skip_ok_unless(core.state['install.orphaned'], 'No orphaned packages')
            # Reinstall packages that we removed but didn't install
            # Technically, this doesn't bring the system back to its original
            # state of packages: we don't track state of EPEL/OSG repos and we
            # leave the ones we drop in
            command = ['yum', '-y', 'install'] + core.state['install.orphaned']
            fail_msg, _, _, _ = yum.retry_command(command)
            if fail_msg:
                self.fail(fail_msg)

    def test_05_restore_mapfile(self):
        if core.state['system.wrote_mapfile']:
            files.restore(core.config['system.mapfile'], 'user')


    def test_06_cleanup_test_certs(self):
        certs_dir = '/etc/grid-security/certificates'
        if core.state['certs.ca_created']:
            files.remove(os.path.join(certs_dir, 'OSG-Test-CA.*'))
            try:
                dirlist = os.listdir(certs_dir)
            except FileNotFoundError:
                dirlist = []
            for link in dirlist:
                abs_link_path = os.path.join(certs_dir, link)
                try:
                    dest = os.readlink(abs_link_path)
                    if re.match(r'OSG-Test-CA\.', dest):
                        files.remove(abs_link_path)
                except OSError as e:
                    if e.errno == errno.EINVAL:
                        continue

            # Remove config files
            openssl_dir = '/etc/pki/'
            for ca_file in ['index.txt*', 'crlnumber*', 'serial*']:
                files.remove(os.path.join(openssl_dir, 'CA', ca_file))
            for tls_file in ['osg-test-ca.conf', 'osg-test-extensions.conf']:
                files.remove(os.path.join(openssl_dir, 'tls', tls_file))

        # Remove the entire certs dir if our test CA was the only resident
        try:
            if len(os.listdir(certs_dir)) == 0:
                files.remove(certs_dir, force=True)
        except FileNotFoundError:
            core.log_message(f'{certs_dir} has already been removed')

        if core.state['certs.hostcert_created']:
            files.remove(core.config['certs.hostcert'])
            files.remove(core.config['certs.hostkey'])

    def test_07_remove_test_user(self):
        if not core.state['general.user_added']:
            core.log_message('Did not add user')
            return

        username = core.options.username
        password_entry = pwd.getpwnam(username)
        globus_dir = os.path.join(password_entry.pw_dir, '.globus')

        # Remove certs in case userdel fails
        if core.state['general.user_cert_created']:
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

    def test_08_remove_scitokens(self):
        for key in core.config:
            if not key.startswith("token."):
                continue
            # token.foo is in core.config, but token.foo_created is in core.state
            if not core.state.get(key + "_created", None):
                # Skipping this token - we may not have created it
                continue
            token_file = core.config[key]
            if os.path.exists(token_file):
                files.remove(token_file)

    # The backups test should always be last, in case any prior tests restore
    # files from backup.
    def test_99_backups(self):
        record_is_clear = True
        if len(files._backups) > 0:
            details = ''
            for backup_id, backup_path in files._backups.items():
                details += "-- Backup of '%s' for '%s' in '%s'\n" % (backup_id[0], backup_id[1], backup_path)
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
