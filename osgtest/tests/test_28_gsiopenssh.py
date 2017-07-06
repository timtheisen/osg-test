from osgtest.library import core
from osgtest.library import osgunittest
from osgtest.library import files
from osgtest.library import service


SSHD_CONFIG = "/etc/gsissh/sshd_config"
SSHD_CONFIG_TEXT = r'''
Port %(port)d
AuthorizedKeysFile .ssh/authorized_keys
UsePrivilegeSeparation sandbox

GSSAPIAuthentication yes
GSSAPIDelegateCredentials yes
GSSAPICleanupCredentials yes
GSSAPIStrictAcceptorCheck yes
GSSAPIKeyExchange yes

RSAAuthentication no
PubkeyAuthentication no
PasswordAuthentication no
ChallengeResponseAuthentication no

Subsystem       sftp    /usr/libexec/gsissh/sftp-server
'''


class TestStartGSIOpenSSH(osgunittest.OSGTestCase):
    def setUp(self):
        core.skip_ok_unless_installed('gsi-openssh-server', 'gsi-openssh-clients')

    def test_01_set_config(self):
        port = core.config['gsissh.port'] = 2222

        files.write(
            SSHD_CONFIG,
            SSHD_CONFIG_TEXT % {'port': port},
            owner='gsissh',
            chmod=0600)

    def test_02_setup_selinux_port(self):
        if not core.state['selinux.mode']:
            self.skip_ok('SELinux disabled')
        core.skip_ok_unless_installed('policycoreutils-python')
        port = core.config['gsissh.port']
        core.check_system(['semanage', 'port', '--add', '-t', 'ssh_port_t', '--proto', 'tcp', str(port)],
                          message="Allow [gsi]sshd to use port %d" % port)

    def test_03_start(self):
        core.state['gsisshd.started-service'] = False
        core.state['gsisshd.can-run'] = True
        if core.el_release() >= 7 and core.state['selinux.mode'] and not core.rpm_is_installed(
                'policycoreutils-python'):
            core.state['gsisshd.can-run'] = False
            self.skip_ok("Can't run with SELinux on EL >= 7 without policycoreutils-python")
        service.check_start('gsisshd')
