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

        for mom_file in ['config', 'layout']:
            files.restore(core.config['torque.mom-%s' % mom_file], 'pbs')
        core.state['torque.pbs-mom-running'] = False

    def test_02_stop_server(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(core.state['torque.pbs-server-started'] == False, 'did not start pbs server')

        service.check_stop('pbs_server')

        if core.state['trqauthd.started-service']:
            service.check_stop('trqauthd')

        files.restore(core.config['torque.pbs-servername-file'], 'pbs')
        files.restore(core.config['torque.pbs-nodes-file'], 'pbs')
        core.state['torque.pbs-server-running'] = False

    def test_03_stop_scheduler(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(core.state['torque.pbs-sched-running'] == False, 'did not start pbs scheduler')

        service.check_stop('pbs_sched')

        core.state['torque.pbs-sched-running'] = False

    def test_04_stop_munge(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(core.state['munge.running'] == False, 'munge not running')

        service.check_stop('munge')

        core.state['munge.running'] = False
        files.restore(core.config['munge.keyfile'], 'pbs')

