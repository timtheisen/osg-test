import os
import shutil

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.voms as voms


class TestStopVOMS(osgunittest.OSGTestCase):

    # ==========================================================================

    def test_01_stop_voms(self):
        voms.skip_ok_unless_installed()
        self.skip_ok_unless(core.state['voms.started-server'], 'did not start server')

        if core.el_release() < 7:
            command = ('service', 'voms', 'stop')
            stdout, _, fail = core.check_system(command, 'Stop VOMS server')
            self.assertEqual(stdout.find('FAILED'), -1, fail)
            self.assert_(not os.path.exists(core.config['voms.lock-file']),
                         'VOMS server lock file still exists')
        else:
            core.check_system(('systemctl', 'stop', 'voms@' + core.config['voms.vo']), 'Stop VOMS server')
            status, _, _ = core.system(('systemctl', 'is-active', 'voms@' + core.config['voms.vo']))
            self.assertNotEqual(status, 0, 'VOMS server still active')

    def test_02_restore_vomses(self):
        voms.skip_ok_unless_installed()

        voms.destroy_lsc(core.config['voms.vo'])
        files.restore('/etc/vomses', 'voms')


    def test_03_remove_vo(self):
        voms.skip_ok_unless_installed()

        if core.rpm_is_installed('voms-admin-server'):
            # Ask VOMS Admin to remove VO
            command = ('voms-admin-configure', 'remove',
                       '--vo', core.config['voms.vo'],
                       '--undeploy-database')
            stdout, _, fail = core.check_system(command, 'Remove VO')
            self.assert_('Database undeployed correctly!' in stdout, fail)
            self.assert_(' succesfully removed.' in stdout, fail)

        # Really remove database
        voms.destroy_db(core.config['voms.vo'], core.config['voms.dbusername'])
        voms.destroy_voms_conf(core.config['voms.vo'])


    def test_04_remove_certs(self):
        core.state['voms.removed-certs'] = False
        # Do the keys first, so that the directories will be empty for the certs.
        core.remove_cert('certs.vomskey')
        core.remove_cert('certs.vomscert')
        core.remove_cert('certs.httpkey')
        core.remove_cert('certs.httpcert')
        core.state['voms.removed-certs'] = True
