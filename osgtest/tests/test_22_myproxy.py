import os
import pwd
import socket
import stat
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.tomcat as tomcat
import osgtest.library.osgunittest as osgunittest
import osgtest.library.certificates as certs

class TestStartmyproxy(osgunittest.OSGTestCase):
    
    def test_01_config_certs(self):
        core.config['certs.hostcert'] = '/etc/grid-security/hostcert.pem'
        core.config['certs.hostkey'] = '/etc/grid-security/hostkey.pem'
        core.config['certs.myproxycert'] = '/etc/grid-security/myproxy/hostcert.pem'
        core.config['certs.myproxykey'] = '/etc/grid-security/myproxy/hostkey.pem'

    def test_02_install_myproxy_certs(self):
        core.skip_ok_unless_installed('myproxy-server')
        myproxycert = core.config['certs.myproxycert']
        myproxykey = core.config['certs.myproxykey']
        self.skip_ok_if(core.check_file_and_perms(myproxycert, 'myproxy', 0644) and
                        core.check_file_and_perms(myproxykey, 'myproxy', 0400),
                        'myproxy cert exists and has proper permissions')
        certs.install_cert('certs.myproxycert', 'certs.hostcert', 'voms', 0644)
        certs.install_cert('certs.myproxykey', 'certs.hostkey', 'voms', 0400)

    def test_03_config_myproxy(self):
        core.skip_ok_unless_installed('myproxy-server')
        conFileContents = files.read('/usr/share/osg-test/myproxy-server.config')
        files.write('/etc/myproxy-server.config',conFileContents, owner='root', backup=True)  
        core.config['myproxy.lock-file']='/var/lock/subsys/myproxy-server'
        
    def test_04_start_myproxy(self):
        core.state['myproxy.started-server'] = False

        core.skip_ok_unless_installed('myproxy-server')
        self.skip_ok_if(os.path.exists(core.config['myproxy-server.lock-file']), 'apparently running')

        command = ('service', '', 'start')
        stdout, _, fail = core.check_system(command, 'Start VOMS service')
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(os.path.exists(core.config['voms.lock-file']),
                     'VOMS server PID file is missing')
        core.state['myproxy.started-server'] = True

    
