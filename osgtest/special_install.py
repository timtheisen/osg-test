import osgtest
import re
import unittest

class TestInstall(unittest.TestCase):

    def test_01_yum_repositories(self):
        pre = ('rpm', '--verify', '--quiet', '--nomd5', '--nosize', '--nomtime')
        status = osgtest.command(pre + ('epel-release',))
        self.assertEqual(status, 0)
        status = osgtest.command(pre + ('osg-release',))
        self.assertEqual(status, 0)

    def test_02_clean_yum(self):
        pre = ('yum', '--enablerepo=*', 'clean')
        status, stdout, stderr = osgtest.syspipe(pre + ('all',))
        fail = osgtest.diagnose('YUM clean all', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        status, stdout, stderr = osgtest.syspipe(pre + ('expire-cache',))
        fail = osgtest.diagnose('YUM clean cache', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    def test_03_install_packages(self):
        install_regexp = re.compile(r'\s+Installing\s+:\s+(\S+)\s+\d')
        osgtest.original_rpms = osgtest.installed_rpms()
        for package in osgtest.options.packages:
            if osgtest.rpm_is_installed(package):
                continue
            command = ['yum', '-y']
            for repo in osgtest.options.extrarepos:
                command.append('--enablerepo=%s' % repo)
            command += ['install', package]
            status, stdout, stderr = osgtest.syspipe(command)
            fail = osgtest.diagnose('Install "%s"' % (package),
                                    status, stdout, stderr)
            self.assertEqual(status, 0, fail)
            status = osgtest.command(('rpm', '--verify', '--quiet', package))
            self.assertEqual(status, 0,
                             "Verifying '%s' failed with exit status %d" %
                             (package, status))

            # Parse output for order of installs
            for line in stdout.strip().split('\n'):
                matches = install_regexp.match(line)
                if matches is not None:
                    osgtest.installed_rpm_list.append(matches.group(1))
