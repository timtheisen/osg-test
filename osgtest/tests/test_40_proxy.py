import osgtest.library.core as core
import unittest

class TestGridProxyInit(unittest.TestCase):

    def test_01_grid_proxy_init(self):
        if not core.rpm_is_installed('globus-proxy-utils'):
            core.skip()
            return
        command = ('grid-proxy-init', '-debug')
        password = core.options.password + '\n'
        core.check_system(command, 'Run grid-proxy-init', user=True,
                          stdin=password)
