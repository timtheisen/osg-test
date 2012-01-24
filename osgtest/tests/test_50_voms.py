import os
import osgtest.library.core as core
import pwd
import socket
import unittest

class TestVOMS(unittest.TestCase):

    def test_01_add_user(self):
        if core.missing_rpm('voms-admin-server', 'voms-admin-client'):
            return

        pwd_entry = pwd.getpwnam(core.options.username)
        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_cert_dn, user_cert_issuer = core.certificate_info(cert_path)
        hostname = socket.getfqdn()

        command = ('voms-admin', '--vo', core.config['voms.vo'],
                   '--host', hostname, '--nousercert', 'create-user',
                   user_cert_dn, user_cert_issuer, 'OSG Test User',
                   'root@localhost')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Add VO user', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    def test_02_voms_proxy_init(self):
        core.state['voms.got-proxy'] = False

        if core.missing_rpm('voms-server', 'voms-clients'):
            return

        command = ('voms-proxy-init', '-voms', core.config['voms.vo'])
        password = core.options.password + '\n'
        status, stdout, stderr = core.syspipe(command, True, password)
        fail = core.diagnose('Run voms-proxy-init', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        core.state['voms.got-proxy'] = True

    def test_03_voms_proxy_info(self):
        if core.missing_rpm('voms-clients'):
            return
        if not core.state['voms.got-proxy']:
            core.skip('no proxy')
            return

        command = ('voms-proxy-info', '-all')
        status, stdout, stderr = core.syspipe(command, True)
        fail = core.diagnose('Run voms-proxy-info', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(('/%s/Role=NULL' % (core.config['voms.vo'])) in stdout,
                     'voms-proxy-info output contains sentinel')

    def test_04_voms_proxy_init(self):
        if core.missing_rpm('voms-server', 'voms-clients'):
            return

        command = ('voms-proxy-init', '-voms', core.config['voms.vo'] + ':/Bogus')
        password = core.options.password + '\n'
        status, stdout, stderr = core.syspipe(command, True, password)
        self.assertNotEqual(status, 0, 'voms-proxy-init fails on bad group')
        self.assert_('Unable to satisfy' in stdout,
                     'voms-proxy-init failure message')

    # Copy of 03 above, to make sure failure did not affect good proxy
    def test_05_voms_proxy_info(self):
        if core.missing_rpm('voms-clients'):
            return
        if not core.state['voms.got-proxy']:
            core.skip('no proxy')
            return

        command = ('voms-proxy-info', '-all')
        status, stdout, stderr = core.syspipe(command, True)
        fail = core.diagnose('Run voms-proxy-info', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(('/%s/Role=NULL' % (core.config['voms.vo'])) in stdout,
                     'voms-proxy-info output extended attribute')
