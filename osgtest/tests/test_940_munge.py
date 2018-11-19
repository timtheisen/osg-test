import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStopMunge(osgunittest.OSGTestCase):

    def test_01_stop_munge(self):
        core.skip_ok_unless_installed('munge')
        self.skip_ok_unless(core.state['munge.started-service'], 'munge not running')
        service.check_stop('munge')
        files.restore(core.config['munge.keyfile'], 'munge')

