from osgtest.library import core
from osgtest.library import service
from osgtest.library import osgunittest

class StartHAVEGED(osgunittest.OSGTestCase):

    def test_start_haveged(self):
        core.skip_ok_unless_installed('haveged')
        service.check_start('haveged')
