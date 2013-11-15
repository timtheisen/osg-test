import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import unittest

class TestGridProxyInit(osgunittest.OSGTestCase):

    def test_01_grid_proxy_init(self):
        core.skip_ok_unless_installed('globus-proxy-utils')
        command = ('grid-proxy-init', '-bits', '1024', '-debug')
        password = core.options.password + '\n'
        core.check_system(command, 'Run grid-proxy-init', user=True,
                          stdin=password)
