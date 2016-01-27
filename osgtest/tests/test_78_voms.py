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

class TestStopVOMS(osgunittest.OSGTestCase):

    # ==========================================================================

    def test_01_stop_voms(self):
        core.skip_ok_unless_installed('voms-server')
        self.skip_ok_unless(core.state['voms.started-server'], 'did not start server')

        command = ('service', 'voms', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop VOMS server')
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(not os.path.exists(core.config['voms.lock-file']),
                     'VOMS server lock file still exists')


    def test_02_restore_vomses(self):
        core.skip_ok_unless_installed('voms-admin-server')

        if os.path.exists(core.config['voms.lsc-dir']):
            shutil.rmtree(core.config['voms.lsc-dir'])
        files.restore('/etc/vomses', 'voms')


    def test_03_remove_vo(self):
        core.skip_ok_unless_installed('voms-admin-server', 'voms-mysql-plugin')

        # Ask VOMS Admin to remove VO
        command = ('voms-admin-configure', 'remove',
                   '--vo', core.config['voms.vo'],
                   '--undeploy-database')
        stdout, _, fail = core.check_system(command, 'Remove VO')
        self.assert_('Database undeployed correctly!' in stdout, fail)
        self.assert_(' succesfully removed.' in stdout, fail)

        # Really remove database
        mysql_statement = "DROP DATABASE `voms_%s`" % (core.config['voms.vo'])
        command = ('mysql', '-u', 'root', '-e', mysql_statement)
        core.check_system(command, 'Drop MYSQL VOMS database')


    def test_04_remove_certs(self):
        core.state['voms.removed-certs'] = False
        # Do the keys first, so that the directories will be empty for the certs.
        core.remove_cert('certs.vomskey')
        core.remove_cert('certs.vomscert')
        core.remove_cert('certs.httpkey')
        core.remove_cert('certs.httpcert')
        core.state['voms.removed-certs'] = True
