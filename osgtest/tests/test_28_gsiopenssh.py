from osgtest.library import core
from osgtest.library import osgunittest
from osgtest.library import files
from osgtest.library import service


SSHD_CONFIG = "/etc/gsissh/sshd_config"
SSHD_CONFIG_TEXT = r'''
Port 2222
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
        files.write(
            SSHD_CONFIG,
            SSHD_CONFIG_TEXT,
            owner='gsissh',
            chmod=0600)

    def test_02_start(self):
        core.state['gsisshd.started-service'] = False
        service.check_start('gsisshd')
