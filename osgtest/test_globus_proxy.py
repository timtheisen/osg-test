import osgtest
import unittest

class TestGlobusProxy(unittest.TestCase):

    def test_01_grid_proxy_init(self):
        if not osgtest.rpm_is_installed('globus-proxy-utils'):
            osgtest.skip()
            return
        command = ['grid-proxy-init', '-debug']
        password = osgtest.options.password + '\n'
        (status, stdout, stderr) = osgtest.syspipe(command, True, password)
        if status != 0:
            print '\n\nSTDOUT:'
            print stdout
            print 'STDERR:'
            print stderr
            print '=' * 10
        self.assertEqual(status, 0)
