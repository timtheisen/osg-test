import os
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
