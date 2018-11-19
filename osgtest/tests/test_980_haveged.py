from osgtest.library import core
from osgtest.library import service
from osgtest.library import osgunittest

class StopHAVEGED(osgunittest.OSGTestCase):

    def test_stop_haveged(self):
        core.skip_ok_unless_installed('haveged')
        service.check_stop('haveged')
