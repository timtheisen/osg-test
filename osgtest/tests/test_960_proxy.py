import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest

class TestGridProxyDestroy(osgunittest.OSGTestCase):

    def test_01_check_proxy(self):
        core.skip_ok_unless_installed('globus-proxy-utils')
        self.skip_ok_unless(core.state['proxy.created'], "didn't create proxy")
        command = ('grid-proxy-destroy', '-debug')
        core.check_system(command, 'Run grid-proxy-destroy', user=True)
