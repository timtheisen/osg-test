import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStopPBS(osgunittest.OSGTestCase):

    required_rpms = ['torque',
                     'torque-mom',
                     'torque-server',
                     'torque-scheduler',
                     'torque-client',
                     'munge']


    def test_01_stop_server(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_unless(core.state['pbs_server.started-service'], 'did not start pbs server')
        service.check_stop('pbs_server')
        files.restore(core.config['torque.pbs-serverdb'], 'pbs')
        files.restore(core.config['torque.pbs-nodes-file'], 'pbs')

    def test_02_stop_trqauthd(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_unless(core.state['trqauthd.started-service'], 'did not start trqauthd')
        service.check_stop('trqauthd')
        files.restore(core.config['torque.pbs-servername-file'], 'pbs')

    def test_03_stop_scheduler(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_unless(core.state['pbs_sched.started-service'], 'did not start pbs scheduler')
        service.check_stop('pbs_sched')

    def test_04_stop_mom(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_unless(core.state['pbs_mom.started-service'], 'did not start pbs mom server')
        service.stop('pbs_mom')

        for mom_file in ['config', 'layout']:
            files.restore(core.config['torque.mom-%s' % mom_file], 'pbs')

    def test_05_stop_munge(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_unless(core.state['munge.started-service'], 'munge not running')
        service.check_stop('munge')
        files.restore(core.config['munge.keyfile'], 'pbs')

