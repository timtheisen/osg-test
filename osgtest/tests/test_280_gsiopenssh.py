from osgtest.library import core
from osgtest.library import osgunittest
from osgtest.library import files
from osgtest.library import service


SSHD_CONFIG = "/etc/gsissh/sshd_config"
SSHD_CONFIG_TEXT = r'''
Port %(port)s
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
        port = core.config['gsisshd.port'] = '2222'
        core.state['gsisshd.can-run'] = (not (
            core.el_release() >= 7 and
            core.state['selinux.mode'] and
            not core.dependency_is_installed("/usr/sbin/semanage")))
        self.skip_ok_unless(core.state['gsisshd.can-run'],
                            "Can't run with SELinux on EL >= 7 without semanage")

        files.write(
            SSHD_CONFIG,
            SSHD_CONFIG_TEXT % {'port': port},
            owner='gsissh',
            chmod=0o600)

    def test_02_setup_selinux_port(self):
        if not core.state['selinux.mode']:
            self.skip_ok('SELinux disabled')
        core.skip_ok_unless_installed("/usr/sbin/semanage", by_dependency=True)
        port = core.config['gsisshd.port']
        core.check_system(['semanage', 'port', '--add', '-t', 'ssh_port_t', '--proto', 'tcp', port],
                          message="Allow [gsi]sshd to use port %s" % port)

    def test_03_start(self):
        core.state['gsisshd.started-service'] = False
        self.skip_ok_unless(core.state['gsisshd.can-run'], "Can't run gsisshd (see above)")
        service.check_start('gsisshd')
