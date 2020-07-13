from osgtest.library import core
from osgtest.library import osgunittest
from osgtest.library import files
from osgtest.library import service


SSHD_CONFIG = "/etc/gsissh/sshd_config"


class TestStopGSIOpenSSH(osgunittest.OSGTestCase):
    def setUp(self):
        core.skip_ok_unless_installed('gsi-openssh-server', 'gsi-openssh-clients')
        self.skip_ok_unless(core.state['gsisshd.can-run'], "Couldn't run gsisshd (see above)")

    def test_01_stop(self):
        service.check_stop('gsisshd')

    def test_02_unset_selinux_port(self):
        if not core.state['selinux.mode']:
            self.skip_ok('no selinux')
        policycoreutils_rpm = "policycoreutils-python" if core.el_release() < 8 else "policycoreutils"
        core.skip_ok_unless_installed(policycoreutils_rpm)
        port = core.config['gsisshd.port']
        core.check_system(['semanage', 'port', '--delete', '--proto', 'tcp', port],
                          message="Forbid [gsi]sshd to use port %s" % port)

    def test_03_restore_config(self):
        files.restore(SSHD_CONFIG, owner='gsissh')
