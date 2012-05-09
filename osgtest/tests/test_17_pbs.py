import os
import osgtest.library.core as core
import unittest

class TestStartPBS(unittest.TestCase):

    def __rpms_present(self):
      """
      Check to make sure needed rpms are installed
      """
      rpm_list = ['torque-mom',
                  'torque-server']
      for rpm in rpm_list:
        if core.missing_rpm(rpm):
          return False
      return True

    def test_01_start_mom(self):
        core.config['torque.mom-lockfile'] = '/var/lock/subsys/pbs_mom'
        core.state['torque.mom-daemon'] = False

        if not self.__rpms_present():
            core.skip('pbs not installed')
            return
        if os.path.exists(core.config['torque.mom-lockfile']):
            core.skip('apparently running')
            return

        command = ('service', 'pbs_mom', 'start')
        stdout, _, fail = core.check_system(command, 'Start pbs mom daemon')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['torque.mom-lockfile']),
                     'PBS mom run lock file missing')
        core.state['torque.mom-daemon'] = True
        core.state['torque.pbs-mom-running'] = True


    def test_02_start_pbs(self):
        core.config['torque.pbs-lockfile'] = '/var/lock/subsys/pbs_server'
        core.state['torque.pbs-server'] = False

        if not self.__rpms_present():
            core.skip('pbs not installed')
            return
        if os.path.exists(core.config['torque.pbs-lockfile']):
            core.skip('apparently running')
            return

        command = ('service', 'pbs_server', 'start')
        stdout, _, fail = core.check_system(command, 'Start pbs server daemon')
        self.assert_(stdout.find('error') == -1, fail)
        self.assert_(os.path.exists(core.config['torque.pbs-lockfile']),
                     'pbs server run lock file missing')
        core.state['torque.pbs-server'] = True
        core.state['torque.pbs-server-running'] = True

