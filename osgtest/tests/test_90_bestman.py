import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

from osgtest.library.core import osgrelease

class TestStopBestman(osgunittest.OSGTestCase):

    @osgrelease(3.3)
    def test_01_stop_bestman(self):
        core.skip_ok_unless_installed('bestman2-server', 'bestman2-client')
        self.skip_ok_unless(core.state['bestman.started-server'], 'bestman server not started')
        service.check_stop('bestman2')

    @osgrelease(3.3)
    def test_02_deconfig_sudoers(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client'):
            return
        files.restore('/etc/sudoers', 'bestman')
