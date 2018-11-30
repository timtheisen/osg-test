import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStartMunge(osgunittest.OSGTestCase):

    def test_01_start_munge(self):
        core.config['munge.keyfile'] = '/etc/munge/munge.key'
        core.state['munge.started-service'] = False
        core.skip_ok_unless_installed('munge')
        self.skip_ok_if(service.is_running('munge'), 'already running')

        files.preserve(core.config['munge.keyfile'], 'munge')
        command = ('/usr/sbin/create-munge-key', '-f',)
        stdout, _, fail = core.check_system(command, 'Create munge key')
        self.assert_(stdout.find('error') == -1, fail)
        service.check_start('munge')
