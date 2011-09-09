import osgtest
import unittest

class TestInstall(unittest.TestCase):

    def test_01_yum_repositories(self):
        status = osgtest.command(['rpm', '--verify', '--quiet', 'epel-release'])
        self.assertEqual(status, 0)
        status = osgtest.command(['rpm', '--verify', '--quiet', 'osg-release'])
        self.assertEqual(status, 0)

    def test_02_install_packages(self):
        osgtest.original_rpms = osgtest.installed_rpms()
        for package in osgtest.options.packages:
            command = ['yum', '-y', '--enablerepo=osg-testing', 'install',
                       package]
            (status, stdout, stderr) = osgtest.syspipe(command)
            self.assertEqual(status, 0,
                             "Installing '%s' failed with exit status %d" %
                             (package, status))
            status = osgtest.command(['rpm', '--verify', '--quiet', package])
            self.assertEqual(status, 0,
                             "Verifying '%s' failed with exit status %d" %
                             (package, status))
