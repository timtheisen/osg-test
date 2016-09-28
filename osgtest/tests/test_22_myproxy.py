import os

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

class TestStartMyProxy(osgunittest.OSGTestCase):

    def test_01_config_certs(self):
        core.config['certs.myproxycert'] = '/etc/grid-security/myproxy/hostcert.pem'
        core.config['certs.myproxykey'] = '/etc/grid-security/myproxy/hostkey.pem'

    def test_02_install_myproxy_certs(self):
        core.skip_ok_unless_installed('myproxy-server')
        myproxycert = core.config['certs.myproxycert']
        myproxykey = core.config['certs.myproxykey']
        self.skip_ok_if(core.check_file_and_perms(myproxycert, 'myproxy', 0644) and
                        core.check_file_and_perms(myproxykey, 'myproxy', 0400),
                        'myproxy cert exists and has proper permissions')
        core.install_cert('certs.myproxycert', 'certs.hostcert', 'myproxy', 0644)
        core.install_cert('certs.myproxykey', 'certs.hostkey', 'myproxy', 0400)

    def test_03_config_myproxy(self):
        core.skip_ok_unless_installed('myproxy-server')
        conFileContents = files.read('/usr/share/osg-test/test_myproxy_server.config')
        files.write('/etc/myproxy-server.config', conFileContents, owner='root', backup=True)
        if core.el_release() <= 6:
            core.config['myproxy.lock-file'] = '/var/lock/subsys/myproxy-server'
        else:
            core.config['myproxy.lock-file'] = '/var/run/myproxy-server/myproxy.pid'

    def test_04_start_myproxy(self):
        core.state['myproxy.started-server'] = False

        core.skip_ok_unless_installed('myproxy-server')
        self.skip_ok_if(os.path.exists(core.config['myproxy.lock-file']), 'apparently running')

        service.start('myproxy-server')
        self.assert_(service.is_running('myproxy-server'), 'MyProxy failed to start')
        core.state['myproxy.started-server'] = True

