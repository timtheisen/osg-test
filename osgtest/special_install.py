import osgtest
import unittest

class TestInstall(unittest.TestCase):

    def test_01_yum_repositories(self):
        pre = ['rpm', '--verify', '--quiet', '--nomd5', '--nosize', '--nomtime']
        status = osgtest.command(pre + ['epel-release'])
        self.assertEqual(status, 0)
        status = osgtest.command(pre + ['osg-release'])
        self.assertEqual(status, 0)

    def test_02_install_packages(self):
        osgtest.original_rpms = osgtest.installed_rpms()
        for package in osgtest.options.packages:
            if osgtest.rpm_is_installed(package):
                continue
            command = ['yum', '-y']
            for repo in osgtest.options.extrarepos:
                command.append('--enablerepo=%s' % repo)
            command += ['install', package]
            (status, stdout, stderr) = osgtest.syspipe(command)
            fail = osgtest.diagnose('Install "%s"' % (package),
                                    status, stdout, stderr)
            self.assertEqual(status, 0, fail)
            status = osgtest.command(['rpm', '--verify', '--quiet', package])
            self.assertEqual(status, 0,
                             "Verifying '%s' failed with exit status %d" %
                             (package, status))
