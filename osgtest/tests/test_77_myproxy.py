import glob
import os
import pwd
import re
import shutil
import socket
import time
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.certificates as certs

class TestStopMyProxy(osgunittest.OSGTestCase):

    # ==========================================================================

    def test_01_stop_myproxy(self):
        core.skip_ok_unless_installed('myproxy-server')
        self.skip_ok_unless(core.state['myproxy.started-server'], 'did not start server')

        command = ('service', 'myproxy-server', 'stop')
        stdout, stderr, fail = core.check_system(command, 'Stop myproxy server')
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(not os.path.exists(core.config['myproxy.lock-file']),
                     'myproxy server lock file still exists')


    def test_02_restore_configFile(self):
        core.skip_ok_unless_installed('myproxy-server')

        files.restore('/etc/myproxy-server.config', 'root')


    def test_03_remove_certs(self):
        core.state['myproxy.removed-certs'] = False
        # Do the keys first, so that the directories will be empty for the certs.
        certs.remove_cert('certs.myproxykey')
        certs.remove_cert('certs.myproxycert')
        core.state['myproxy.removed-certs'] = True
