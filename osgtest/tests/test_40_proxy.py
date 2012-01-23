import osgtest.library.core as core
import unittest

class TestGridProxyInit(unittest.TestCase):

    def test_01_grid_proxy_init(self):
        if not core.rpm_is_installed('globus-proxy-utils'):
            core.skip()
            return
        command = ('grid-proxy-init', '-debug')
        password = core.options.password + '\n'
        status, stdout, stderr = core.syspipe(command, True, password)
        fail = core.diagnose('Run grid-proxy-init', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
