import glob
import os
import osgtest.library.core as core
import pwd
import re
import shutil
import socket
import time
import unittest

class TestStopVOMS(unittest.TestCase):

    # Carefully removes a certificate with the given key.  Removes all
    # paths associated with the key, as created by the install_cert()
    # function.
    def remove_cert(self, target_key):
        if core.state.has_key(target_key):
            os.remove(core.state[target_key])
        if core.state.has_key(target_key + '-backup'):
            shutil.move(core.state[target_key + '-backup'],
                        core.state[target_key])
        if core.state.has_key(target_key + '-dir'):
            target_dir = core.state[target_key + '-dir']
            if len(os.listdir(target_dir)) == 0:
                os.rmdir(target_dir)

    # ==========================================================================

    def test_01_stop_voms(self):
        if not core.rpm_is_installed('voms-server'):
            core.skip('not installed')
            return
        if not core.state['voms.started-server']:
            core.skip('did not start server')
            return

        command = ('service', 'voms', 'stop')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Stop VOMS service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(not os.path.exists(core.config['voms.lock-file']),
                     'VOMS server lock file still exists')

    def test_02_restore_vomses(self):
        if os.path.isdir(core.config['voms.lsc-dir']):
            shutil.rmtree(core.config['voms.lsc-dir'])
        if core.state['voms.installed-vomses']:
            os.remove('/etc/vomses')
        if os.path.exists('/etc/vomses.osg-test.backup'):
            shutil.move('/etc/vomses.osg-test.backup', '/etc/vomses')

    def test_03_remove_vo(self):
        if core.missing_rpm('voms-admin-server', 'voms-mysql-plugin'):
            return

        # Ask VOMS Admin to remove VO
        db_user_name = 'admin-' + core.config['voms.vo']
        command = ('voms-admin-configure', 'remove',
                   '--vo', core.config['voms.vo'],
                   '--undeploy-database')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Remove VO', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_('Database undeployed correctly!' in stdout, fail)
        self.assert_(' succesfully removed.' in stdout, fail)

        # Really remove database
        mysql_statement = "DROP DATABASE `voms_%s`" % (core.config['voms.vo'])
        command = ('mysql', '-u', 'root', '-e', mysql_statement)
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Drop MYSQL VOMS database',
                             status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    # Do the keys first, so that the directories will be empty for the certs.
    def test_04_remove_certs(self):
        self.remove_cert('certs.vomskey')
        self.remove_cert('certs.vomscert')
        self.remove_cert('certs.httpkey')
        self.remove_cert('certs.httpcert')
