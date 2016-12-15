import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.mysql as mysql
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStopSlurm(osgunittest.OSGTestCase):

    def slurm_reqs(self):
        core.skip_ok_unless_installed(*core.SLURM_PACKAGES)

    def test_01_stop_slurm(self):
        self.slurm_reqs()
        self.skip_ok_unless(core.state['%s.started-service' % core.config['slurm.service-name']], 'did not start slurm')
        service.check_stop(core.config['slurm.service-name']) # service requires config so we stop it first
        files.restore(core.config['slurm.config'], 'slurm')

    def test_02_stop_slurmdbd(self):
        self.slurm_reqs()
        core.skip_ok_unless_installed('slurm-slurmdbd')
        self.skip_ok_unless(core.state['slurmdbd.started-service'], 'did not start slurmdbd')
        # service requires config so we stop it first; use stop() since slurmdbd fails to remove pid file
        service.stop('slurmdbd')
        files.restore(core.config['slurmdbd.config'], 'slurm')
        mysql.check_execute("drop database %s; " % core.config['slurmdbd.name'] + \
                            "drop user %s;" % core.config['slurmdbd.user'],
                            'drop mysql slurmdb')

