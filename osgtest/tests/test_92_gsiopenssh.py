from osgtest.library import core
from osgtest.library import osgunittest
from osgtest.library import files
from osgtest.library import service


SSHD_CONFIG = "/etc/gsissh/sshd_config"


class TestStopGSIOpenSSH(osgunittest.OSGTestCase):
    def setUp(self):
        core.skip_ok_unless_installed('gsi-openssh-server', 'gsi-openssh-clients')

    def test_01_stop(self):
        service.check_stop('gsisshd')

    def test_02_restore_config(self):
        files.restore(SSHD_CONFIG, owner='gsissh')
