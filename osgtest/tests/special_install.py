import re
import time

import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest

class TestInstall(osgunittest.OSGTestCase):

    def clean_yum(self):
        deadline = time.time() + 3600
        pre = ('yum', '--enablerepo=*', 'clean')
        self.retry_command(pre + ('all',), deadline)
        self.retry_command(pre + ('expire-cache',), deadline)

    def parse_output_for_packages(self, stdout):
        install_regexp = re.compile(r'\s+Installing\s+:\s+\d*:?(\S+)\s+\d')
        update_regexp = re.compile(r'\s+Updating\s+:\s+\d*:?(\S+)\s+\d')
        for line in stdout:
            install_matches = install_regexp.match(line)
            update_matches = update_regexp.match(line)
            if install_matches is not None:
                core.state['install.installed'].append(install_matches.group(1))
            if update_matches is not None:
                core.state['install.updated'].append(update_matches.group(1))

    def retry_command(self, command, deadline):
        fail_msg, status, stdout, stderr = '', '', '', ''
        # Loop for retries
        while True:
            
            # Stop (re)trying if the deadline has passed
            if time.time() > deadline:
                fail_msg += "Retries terminated after timeout period" 
                break

            status, stdout, stderr = core.system(command)

            # Deal with success
            if status == 0:
                break

            # Deal with failures that can be retried
            elif self.yum_failure_can_be_retried(stdout):
                time.sleep(30)
                core.log_message("Retrying command")
                continue

            # Otherwise, we do not expect a retry to succeed, ever, so fail
            # this package
            else:
                fail_msg = core.diagnose("Command failed", status, stdout, stderr)
                break
            
        return fail_msg, status, stdout, stderr
                
    def yum_failure_can_be_retried(self, output):
        """Scan yum output to see if a retry might succeed."""
        whitelist = [r'Error Downloading Packages:\n.*No more mirrors to try',
                     r'Could not retrieve mirrorlist.*\nerror was \[Errno 12\] Timeout: <urlopen error timed out>']
        for regex in whitelist:
            if re.search(regex, output):
                return True
        return False

    def get_yum_transaction_id(self):
        """Grab the latest transaction ID from yum"""
        command = ('yum', 'history', 'info')
        history_out = core.check_system(command, 'Get yum Transaction ID')[0]
        m = re.search('Transaction ID : (\d*)', history_out)
        return m.group(1)

    def test_01_yum_repositories(self):
        pre = ('rpm', '--verify', '--nomd5', '--nosize', '--nomtime')
        core.check_system(pre + ('epel-release',), 'Verify epel-release')
        # If osg-release isn't installed, try osg-release-itb
        try:
            core.check_system(pre + ('osg-release',), 'Verify osg-release')
        except AssertionError:
            core.check_system(pre + ('osg-release-itb',), 'Verify osg-release + osg-release-itb')

    def test_02_clean_yum(self):
        self.clean_yum()

    def test_03_install_packages(self):
        core.state['install.success'] = False
        core.state['install.installed'] = []
        core.state['install.updated'] = []

        # Install packages
        core.state['install.transaction_ids'] = []
        fail_msg = ''
        deadline = time.time() + 3600   # 1 hour from now
        for package in core.options.packages:

            # Do not try to re-install packages
            if core.rpm_is_installed(package):
                continue

            # Attempt installation
            command = ['yum', '-y']
            for repo in core.options.extrarepos:
                command.append('--enablerepo=%s' % repo)
            command += ['install', package]

            retry_fail, status, stdout, stderr = self.retry_command(command, deadline)
            if retry_fail == '':
            # This means retry the command succeeded
                if core.el_release() == 6:
                    # RHEL 6 does not have the rollback option, so store the
                    # transaction IDs so we can undo each transaction in the
                    # proper order
                    core.state['install.transaction_ids'].append(self.get_yum_transaction_id())
                command = ('rpm', '--verify', package)
                core.check_system(command, 'Verify %s' % (package))
                self.parse_output_for_packages(stdout.strip().split('\n'))

            fail_msg += retry_fail
                
        if fail_msg:
            self.fail(fail_msg)
        core.state['install.success'] = True

    def test_04_update_osg_release(self):
        if not (core.options.updaterelease):
            return

        core.state['install.release-updated'] = False
        self.skip_bad_unless(core.state['install.success'], 'Install did not succeed')

        core.config['install.original-release-ver'] = core.osg_release(self)

        command = ['rpm', '-e', 'osg-release']
        core.check_system(command, 'Erase osg-release')
        
        self.assert_(re.match('\d+\.\d+', core.options.updaterelease), "Unrecognized updaterelease format")
        rpm_url = 'http://repo.grid.iu.edu/osg/' + core.options.updaterelease + '/osg-' + core.options.updaterelease \
            + '-el' + str(core.el_release()) + '-release-latest.rpm'
        command = ['rpm', '-Uvh', rpm_url]
        core.check_system(command, 'Update osg-release')
        self.clean_yum()
        
        # If update repos weren't specified, just use osg-release
        if not core.options.updaterepo:
            core.options.updaterepo = 'osg'

        core.state['install.release-updated'] = True
        
    def test_05_update_packages(self):
        if not (core.options.updaterepo and core.state['install.installed']):
            return
        
        self.skip_bad_unless(core.state['install.success'], 'Install did not succeed')

        # Update packages
        deadline = time.time() + 3600   # 1 hour from now

        command = ['yum', 'update', '-y']
        command.append('--enablerepo=%s' % core.options.updaterepo)
        for package in core.state['install.installed']:
            command += [package]

        fail_msg, status, stdout, stderr = self.retry_command(command, deadline)
        self.parse_output_for_packages(stdout.strip().split('\n'))

        if fail_msg:
            self.fail(fail_msg)

    def test_06_fix_java_symlinks(self):
        # This implements Section 5.1.2 of
        # https://twiki.opensciencegrid.org/bin/view/Documentation/Release3/InstallSoftwareWithOpenJDK7
        java7 = 'java-1.7.0-openjdk'
        java7_devel = 'java-1.7.0-openjdk-devel'

        # We don't use skip_ok_unless_installed because we want to limit the number of ok skips
        jdk_installed = False
        command = ('rpm', '--query', 'jdk')
        _, stdout, _ = core.system(command)
        if re.search("^jdk-1\.6\.\d+_\d+.*", stdout):
            jdk_installed = True

        if (jdk_installed and core.rpm_is_installed(java7) and core.rpm_is_installed(java7_devel)):
            command = ('rm', '-f', '/usr/bin/java', '/usr/bin/javac', '/usr/bin/javadoc', '/usr/bin/jar')
            core.check_system(command, 'Remove old symlinks')

            command = ('yum', 'reinstall', '-y', java7, java7_devel)
            core.check_system(command, 'Reinstall java7')
        
