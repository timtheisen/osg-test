import osgtest.library.core as core
import re
import unittest

class TestInstall(unittest.TestCase):

    def test_01_yum_repositories(self):
        pre = ('rpm', '--verify', '--quiet', '--nomd5', '--nosize', '--nomtime')
        core.check_system(pre + ('epel-release',), 'Verify epel-release')
        core.check_system(pre + ('osg-release',), 'Verify osg-release')

    def test_02_clean_yum(self):
        pre = ('yum', '--enablerepo=*', 'clean')
        core.check_system(pre + ('all',), 'YUM clean all')
        core.check_system(pre + ('expire-cache',), 'YUM clean cache')

    def test_03_install_packages(self):
        install_regexp = re.compile(r'\s+Installing\s+:\s+(\S+)\s+\d')
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
                matches = install_regexp.match(line)
                if matches is not None:
                    core.state['install.installed'].append(matches.group(1))
