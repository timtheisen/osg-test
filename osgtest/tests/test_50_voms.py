import os
import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import pwd
import socket
import unittest

class TestVOMS(osgunittest.OSGTestCase):

    def test_01_add_user(self):
        core.skip_ok_unless_installed('voms-admin-server', 'voms-admin-client')

        pwd_entry = pwd.getpwnam(core.options.username)
        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_cert_dn, user_cert_issuer = core.certificate_info(cert_path)
        hostname = socket.getfqdn()

        command = ('voms-admin', '--vo', core.config['voms.vo'],
                   '--host', hostname, '--nousercert', 'create-user',
                   user_cert_dn, user_cert_issuer, 'OSG Test User',
                   'root@localhost')
        core.check_system(command, 'Add VO user')

    def test_02_voms_proxy_init(self):
        core.state['voms.got-proxy'] = False

        core.skip_ok_unless_installed('voms-admin-server', 'voms-admin-client')

        command = ('voms-proxy-init', '-voms', core.config['voms.vo'])
        password = core.options.password + '\n'
        core.check_system(command, 'Run voms-proxy-init', user=True,
                          stdin=password)
        core.state['voms.got-proxy'] = True

    def test_03_voms_proxy_info(self):
        core.skip_ok_unless_installed('voms-clients')
        self.skip_bad_unless(core.state['voms.got-proxy'], 'no proxy')

        command = ('voms-proxy-info', '-all')
        stdout = core.check_system(command, 'Run voms-proxy-info',
                                   user=True)[0]
        self.assert_(('/%s/Role=NULL' % (core.config['voms.vo'])) in stdout,
                     'voms-proxy-info output contains sentinel')

    def test_04_voms_proxy_init(self):
        core.skip_ok_unless_installed('voms-server', 'voms-clients')

        command = ('voms-proxy-init', '-voms', core.config['voms.vo'] + ':/Bogus')
        password = core.options.password + '\n'
        status, stdout, stderr = core.system(command, True, password)
        self.assertNotEqual(status, 0, 'voms-proxy-init fails on bad group')
        self.assert_('Unable to satisfy' in stdout,
                     'voms-proxy-init failure message')

    # Copy of 03 above, to make sure failure did not affect good proxy
    def test_05_voms_proxy_info(self):
        core.skip_ok_unless_installed('voms-clients')
        self.skip_bad_unless(core.state['voms.got-proxy'], 'no proxy')

        command = ('voms-proxy-info', '-all')
        stdout = core.check_system(command, 'Run voms-proxy-info',
                                   user=True)[0]
        self.assert_(('/%s/Role=NULL' % (core.config['voms.vo'])) in stdout,
                     'voms-proxy-info output extended attribute')
