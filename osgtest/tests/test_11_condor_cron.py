import os
import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import unittest

class TestStartCondorCron(osgunittest.OSGTestCase):

    def test_01_start_condor_cron(self):
        core.config['condor-cron.lockfile'] = '/var/lock/subsys/condor-cron'
        core.state['condor-cron.started-service'] = False
        core.state['condor-cron.running-service'] = False

        core.skip_ok_unless_installed('condor-cron')
        if os.path.exists(core.config['condor-cron.lockfile']):
            core.state['condor-cron.running-service'] = True
            self.skip_ok('already running')

        if core.el_release() < 7:
            command = ('service', 'condor-cron', 'start')
            stdout, _, fail = core.check_system(command, 'Start Condor-Cron')
            self.assert_(stdout.find('error') == -1, fail)
            self.assert_(os.path.exists(core.config['condor-cron.lockfile']),
                         'Condor-Cron run lock file missing')
        else:
            core.check_system(('systemctl', 'start', 'condor-cron'), 'Start Condor-Cron')
            core.check_system(('systemctl', 'is-active', 'condor-cron'), 'Verify status of Condor-Cron')

        core.state['condor-cron.started-service'] = True
        core.state['condor-cron.running-service'] = True
