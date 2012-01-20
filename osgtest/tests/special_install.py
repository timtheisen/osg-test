import osgtest.library.core as core
import re
import unittest

class TestInstall(unittest.TestCase):

    def test_01_yum_repositories(self):
        pre = ('rpm', '--verify', '--quiet', '--nomd5', '--nosize', '--nomtime')
        status = core.command(pre + ('epel-release',))
        self.assertEqual(status, 0)
        status = core.command(pre + ('osg-release',))
        self.assertEqual(status, 0)

    def test_02_clean_yum(self):
        pre = ('yum', '--enablerepo=*', 'clean')
        status, stdout, stderr = core.syspipe(pre + ('all',))
        fail = core.diagnose('YUM clean all', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        status, stdout, stderr = core.syspipe(pre + ('expire-cache',))
        fail = core.diagnose('YUM clean cache', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    def test_03_install_packages(self):
        install_regexp = re.compile(r'\s+Installing\s+:\s+(\S+)\s+\d')
        core.original_rpms = core.installed_rpms()
        for package in core.options.packages:
            if core.rpm_is_installed(package):
                continue
            command = ['yum', '-y']
            for repo in core.options.extrarepos:
                command.append('--enablerepo=%s' % repo)
            command += ['install', package]
            status, stdout, stderr = core.syspipe(command)
            fail = core.diagnose('Install "%s"' % (package),
                                    status, stdout, stderr)
            self.assertEqual(status, 0, fail)
            status = core.command(('rpm', '--verify', '--quiet', package))
            self.assertEqual(status, 0,
                             "Verifying '%s' failed with exit status %d" %
                             (package, status))

            # Parse output for order of installs
            for line in stdout.strip().split('\n'):
                matches = install_regexp.match(line)
                if matches is not None:
                    core.installed_rpm_list.append(matches.group(1))
