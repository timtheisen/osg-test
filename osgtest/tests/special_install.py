import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import re
import unittest

class TestInstall(osgunittest.OSGTestCase):
    install_regexp = re.compile(r'\s+Installing\s+:\s+\d*:?(\S+)\s+\d')
    
    def test_01_yum_repositories(self):
        pre = ('rpm', '--verify', '--quiet', '--nomd5', '--nosize', '--nomtime')
        core.check_system(pre + ('epel-release',), 'Verify epel-release')
        core.check_system(pre + ('osg-release',), 'Verify osg-release')

    def test_02_clean_yum(self):
        pre = ('yum', '--enablerepo=*', 'clean')
        core.check_system(pre + ('all',), 'YUM clean all')
        core.check_system(pre + ('expire-cache',), 'YUM clean cache')

    def test_03_install_packages(self):
        core.state['install.success'] = False
        core.state['install.preinstalled'] = core.installed_rpms()
        core.state['install.installed'] = []
        for package in core.options.packages:
            if core.rpm_is_installed(package):
                continue
            command = ['yum', '-y']
            for repo in core.options.extrarepos:
                command.append('--enablerepo=%s' % repo)
            command += ['install', package]
            stdout = core.check_system(command, 'Install %s' % (package))[0]
            command = ('rpm', '--verify', '--quiet', package)
            core.check_system(command, 'Verify %s' % (package))

            # Parse output for order of installs
            for line in stdout.strip().split('\n'):
                matches = self.install_regexp.match(line)
                if matches is not None:
                    core.state['install.installed'].append(matches.group(1))
        core.state['install.success'] = True

    def test_04_update_packages(self):
        if not (core.options.updaterepo and core.state['install.installed']):
            return
        
        self.skip_bad_unless(core.state['install.success'], 'Install did not succeed')

        update_regexp = re.compile(r'\s+Updating\s+:\s+\d*:?(\S+)\s+\d')
        core.state['install.updated'] = []
        command = ['yum', 'update', '-y']
        command.append('--enablerepo=%s' % core.options.updaterepo)
        for package in core.state['install.installed']:
            command += [package]
        stdout = core.check_system(command, 'Update packages')[0]

        # Parse output for order of installs and to differentiate between update and installs
        for line in stdout.strip().split('\n'):
            install_matches = self.install_regexp.match(line)
            update_matches = update_regexp.match(line)
            if install_matches is not None:
                core.state['install.installed'].append(install_matches.group(1))
            elif update_matches is not None:
                core.state['install.updated'].append(update_matches.group(1))

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
        
