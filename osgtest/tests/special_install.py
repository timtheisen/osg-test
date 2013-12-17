import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import osgtest.library.files as files
import re
import time
import unittest

class TestInstall(osgunittest.OSGTestCase):
    install_regexp = re.compile(r'\s+Installing\s+:\s+\d*:?(\S+)\s+\d')
    
    def test_01_yum_repositories(self):
        pre = ('rpm', '--verify', '--nomd5', '--nosize', '--nomtime')
        core.check_system(pre + ('epel-release',), 'Verify epel-release')
        # If osg-release isn't installed, try osg-release-itb
        try:
            core.check_system(pre + ('osg-release',), 'Verify osg-release')
        except AssertionError:
            core.check_system(pre + ('osg-release-itb',), 'Verify osg-release + osg-release-itb')

    def test_02_clean_yum(self):
        pre = ('yum', '--enablerepo=*', 'clean')
        core.check_system(pre + ('all',), 'YUM clean all')
        core.check_system(pre + ('expire-cache',), 'YUM clean cache')

    def test_03_install_packages(self):
        core.state['install.success'] = False

        # Grab pre-install state
        el_version = core.el_release()
        if el_version == 5:
            # enable rollback
            core.config['install.yum_conf'] = '/etc/yum.conf'
            core.config['install.rpm_macros'] = '/etc/rpm/macros'
            files.append(core.config['install.yum_conf'], 'tsflags=repackage', owner='install')
            files.append(core.config['install.rpm_macros'], '%_repackage_all_erasures 1', owner='install')
            core.state['install.rollback_time'] = time.strftime('%F %H:%M:%S')

        # Install packages
        core.state['install.installed'] = []
        core.state['install.transaction_ids'] = []
        failed = []
        for package in core.options.packages:
            if core.rpm_is_installed(package):
                continue
            command = ['yum', '-y']
            for repo in core.options.extrarepos:
                command.append('--enablerepo=%s' % repo)
            command += ['install', package]
            status, stdout, sterr = core.system(command)

            if status != 0:
                failed.append(package)
            else:
                # RHEL6 doesn't have the rollback option so we have to store the transaction id's so
                # we can undo each transaction in the proper order
                if el_version == 6:
                    command = ('yum', 'history', 'info')
                    history_out = core.check_system(command, 'Get yum Transaction ID')[0]
                    m = re.search('Transaction ID : (\d*)', history_out)
                    core.state['install.transaction_ids'].append(m.group(1))

                command = ('rpm', '--verify', package)
                core.check_system(command, 'Verify %s' % (package))

                # Parse output for order of installs
                for line in stdout.strip().split('\n'):
                    matches = self.install_regexp.match(line)
                    if matches is not None:
                        core.state['install.installed'].append(matches.group(1))
        if failed:
            fail_msg = 'Install:'
            for package in failed:
                fail_msg = fail_msg + ' %s' % package
            self.fail(fail_msg)
        core.state['install.success'] = True

    def test_04_update_osg_release(self):
        if not (core.options.updaterelease):
            return

        self.skip_bad_unless(core.state['install.success'], 'Install did not succeed')

        command = ['rpm', '-e', 'osg-release']
        core.check_system(command, 'Erase osg-release')
        
        self.assert_(re.match('\d+\.\d+', core.options.updaterelease), "Unrecognized updaterelease format")
        rpm_url = 'http://repo.grid.iu.edu/osg/' + core.options.updaterelease + '/osg-' + core.options.updaterelease \
            + '-el' + str(core.el_release()) + '-release-latest.rpm'
        command = ['rpm', '-Uvh', rpm_url]
        core.check_system(command, 'Update osg-release')
        
        # If update repos weren't specified, just use osg-release
        if not core.options.updaterepo:
            core.options.updaterepo='osg'
        
    def test_04_update_packages(self):
        if not (core.options.updaterepo and core.state['install.installed']):
            return
        
        self.skip_bad_unless(core.state['install.success'], 'Install did not succeed')

        update_regexp = re.compile(r'\s+Updating\s+:\s+\d*:?(\S+)\s+\d')
        command = ['yum', 'update', '-y']
        command.append('--enablerepo=%s' % core.options.updaterepo)
        for package in core.state['install.installed']:
            command += [package]
        stdout = core.check_system(command, 'Update packages')[0]

        # Parse output for order of installs and to differentiate between update and installs
        for line in stdout.strip().split('\n'):
            if self.install_regexp.match(line) is not None:
                core.state['install.installed'].append(install_matches.group(1))

    def test_05_fix_java_symlinks(self):
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
        
