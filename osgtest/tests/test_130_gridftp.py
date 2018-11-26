import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStartGridFTP(osgunittest.OSGTestCase):

    def test_01_start_gridftp(self):
        core.state['gridftp.started-server'] = False
        core.state['gridftp.running-server'] = False

        core.skip_ok_unless_installed('globus-gridftp-server-progs')
        if service.is_running('globus-gridftp-server'):
            core.state['gridftp.running-server'] = True
            return

        service.check_start('globus-gridftp-server')
        core.state['gridftp.running-server'] = True
        core.state['gridftp.started-server'] = True
    
    def test_03_configure_cksums_dir(self):
        core.skip_ok_unless_installed('gridftp-hdfs')
        checksums_dir = '/cksums'
        command = ('mkdir', '-p', checksums_dir)
        core.check_system(command, 'Creating gridftp hadoop cheksums dir')
        
        command= ('chmod', 'a+w', checksums_dir)
        core.check_system(command, 'Making checksums dir writable')
