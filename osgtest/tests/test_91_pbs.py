import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStopPBS(osgunittest.OSGTestCase):

    required_rpms = ['torque-mom',
                     'torque-server',
                     'torque-scheduler',
                     'torque-client',
                     'munge']

    def test_01_stop_mom(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(core.state['torque.pbs-mom-running'] == False, 'did not start pbs mom server')

        service.stop('pbs_mom')
        self.assert_(not service.is_running('pbs_mom'), 'PBS mom failed to stop')

        for mom_file in ['config', 'layout']:
            files.restore(core.config['torque.mom-%s' % mom_file], 'pbs')
        core.state['torque.pbs-mom-running'] = False

    def test_02_stop_server(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(core.state['torque.pbs-server-started'] == False, 'did not start pbs server')

        service.stop('pbs_server')
        self.assert_(not service.is_running('pbs_server'), 'PBS server failed to stop')

        if core.state['trqauthd.started-service']:
            service.stop('trqauthd')

        files.restore(core.config['torque.pbs-servername-file'], 'pbs')
        files.restore(core.config['torque.pbs-nodes-file'], 'pbs')
        core.state['torque.pbs-server-running'] = False

    def test_03_stop_scheduler(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(core.state['torque.pbs-sched-running'] == False, 'did not start pbs scheduler')

        service.stop('pbs_sched')
        self.assert_(not service.is_running('pbs_sched'), 'PBS sched failed to stop')

        core.state['torque.pbs-sched-running'] = False

    def test_04_stop_munge(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(core.state['munge.running'] == False, 'munge not running')

        service.stop('munge')
        self.assert_(not service.is_running('munge'), 'munge failed to stop')

        core.state['munge.running'] = False
        files.restore(core.config['munge.keyfile'], 'pbs')

