import os
import unittest

import osgtest.library.core as core

class TestSetupVomsAdmin(unittest.TestCase):

    def test_01_wait_for_voms_admin(self):
        core.state['voms.started-webapp'] = False

        if core.missing_rpm('voms-admin-server'):
            return

        line, gap = core.monitor_file(core.config['voms.webapp-log'],
                                      core.state['voms.webapp-log-stat'],
                                      'VOMS-Admin started succesfully', 60.0)
        self.assert_(line is not None, 'VOMS Admin webapp started')
        core.state['voms.started-webapp'] = True
        core.log_message('VOMS Admin started after %.1f seconds' % gap)

    def test_02_open_access(self):
        if core.missing_rpm('voms-admin-server', 'voms-admin-client'):
            return
        if not core.state['voms.started-webapp']:
            core.skip('VOMS Admin webapp not started')
            return

        command = ('voms-admin', '--nousercert',
                   '--vo', core.config['voms.vo'],
                   'add-ACL-entry', '/' + core.config['voms.vo'], 'ANYONE',
                   'VOMS_CA', 'CONTAINER_READ,MEMBERSHIP_READ', 'true')
        core.check_system(command, 'Add VOMS Admin ACL entry')
