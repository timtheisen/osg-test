import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import pprint
import errno

class TestGridProxyInit(osgunittest.OSGTestCase):

    def test_00_list_proxies(self):
        command = ('ls', '-lF', '/tmp/x509up_u*')
        status, stdout, _ = core.system(command, 'List proxies')
        core.log_message(stdout)

    def test_01_grid_proxy_init(self):
        core.skip_ok_unless_installed('globus-proxy-utils')
        command = ('grid-proxy-init', '-debug')
        password = core.options.password + '\n'
        try:
            core.check_system(command, 'Run grid-proxy-init', user=True,
                              stdin=password)
        except OSError, e:
            attributes = {}
            for x in dir(e):
                attributes[x] = getattr(e,x, None)
            pprint.pprint(attributes)
            raise

    def test_02_grid_proxy_info(self):
        core.skip_ok_unless_installed('globus-proxy-utils')
        command = ('grid-proxy-info', '-debug')
        core.check_system(command, 'Run grid-proxy-info', user=True)
