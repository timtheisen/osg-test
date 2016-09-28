import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStopMyProxy(osgunittest.OSGTestCase):


    def test_01_stop_myproxy(self):
        core.skip_ok_unless_installed('myproxy-server')
        self.skip_ok_unless(core.state['myproxy.started-server'], 'did not start server')

        service.stop('myproxy-server')
        self.assert_(not service.is_running('myproxy-server'), 'MyProxy failed to stop')


    def test_02_restore_configFile(self):
        core.skip_ok_unless_installed('myproxy-server')

        files.restore('/etc/myproxy-server.config', 'root')


    def test_03_remove_certs(self):
        core.state['myproxy.removed-certs'] = False
        # Do the keys first, so that the directories will be empty for the certs.
        core.remove_cert('certs.myproxykey')
        core.remove_cert('certs.myproxycert')
        core.state['myproxy.removed-certs'] = True
