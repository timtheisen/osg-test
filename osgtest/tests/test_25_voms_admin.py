import os
import unittest

import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest

class TestSetupVomsAdmin(osgunittest.OSGTestCase):

    def test_01_wait_for_voms_admin(self):
        core.state['voms.started-webapp'] = False

        core.skip_ok_unless_installed('voms-admin-server')

        line, gap = core.monitor_file(core.config['voms.webapp-log'], core.state['voms.webapp-log-stat'],
                                      'VOMS-Admin started succesfully', 120.0)
        self.assert_(line is not None, 'VOMS Admin webapp started')
        core.state['voms.started-webapp'] = True
        core.log_message('VOMS Admin started after %.1f seconds' % gap)

    def test_02_open_access(self):
        core.skip_ok_unless_installed('voms-admin-server', 'voms-admin-client')
        self.skip_ok_unless(core.state['voms.started-webapp'], 'VOMS Admin webapp not started')

        command = ('voms-admin', '--nousercert', '--vo', core.config['voms.vo'], 'add-ACL-entry',
                   '/' + core.config['voms.vo'], 'ANYONE', 'VOMS_CA', 'CONTAINER_READ,MEMBERSHIP_READ', 'true')
        core.check_system(command, 'Add VOMS Admin ACL entry')
