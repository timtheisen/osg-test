import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

from osgtest.library.core import osgrelease

class TestStartBestman(osgunittest.OSGTestCase):

    @osgrelease(3.3)
    def test_01_config_certs(self):
        core.config['certs.httpcert'] = '/etc/grid-security/http/httpcert.pem'
        core.config['certs.httpkey'] = '/etc/grid-security/http/httpkey.pem'
        core.config['certs.bestmancert'] = '/etc/grid-security/bestman/bestmancert.pem'
        core.config['certs.bestmankey'] = '/etc/grid-security/bestman/bestmankey.pem'

    @osgrelease(3.3)
    def test_02_install_bestman_certs(self):
        core.skip_ok_unless_installed('bestman2-server', 'bestman2-client', 'gums-service')
        if os.path.exists(core.config['certs.bestmancert']) and os.path.exists(core.config['certs.bestmankey']):
            return
        core.install_cert('certs.bestmancert', 'certs.hostcert', 'bestman', 0o644)
        core.install_cert('certs.bestmankey', 'certs.hostkey', 'bestman', 0o400)

    @osgrelease(3.3)
    def test_03_modify_sudoers(self):
        core.skip_ok_unless_installed('bestman2-server', 'bestman2-client', 'gums-service')
        sudoers_path = '/etc/sudoers'
        contents = files.read(sudoers_path)
        srm_cmd = 'Cmnd_Alias SRM_CMD = /bin/rm, /bin/mkdir, /bin/rmdir, /bin/mv, /bin/cp, /bin/ls'
        srm_usr = 'Runas_Alias SRM_USR = ALL, !root'
        bestman_perm = 'bestman   ALL=(SRM_USR) NOPASSWD: SRM_CMD'
        require_tty = 'Defaults    requiretty'
        had_srm_cmd_line = False
        had_requiretty_commented = False
        for line in contents:
            if require_tty in line:
                if line.startswith("#"):
                    had_requiretty_commented = True
            if srm_cmd in line:
                had_srm_cmd_line =  True
        new_contents = []
        for line in contents:
            if not had_requiretty_commented:
                if line.strip() == require_tty.strip():
                    new_contents += '#'+line+'\n'
                else:
                    new_contents += line.strip()+'\n'
        if not had_srm_cmd_line:
            new_contents += srm_cmd+'\n'
            new_contents += srm_usr+'\n'
            new_contents += bestman_perm+'\n'
        if not had_srm_cmd_line or not had_requiretty_commented:
            files.write(sudoers_path, new_contents, owner='bestman')

    @osgrelease(3.3)
    def test_04_modify_bestman_conf(self):
        core.skip_ok_unless_installed('bestman2-server', 'bestman2-client', 'gums-service')

        bestman_rc_path = '/etc/bestman2/conf/bestman2.rc'
        old_port = 'securePort=8443'
        new_port = 'securePort=10443'
        files.replace(bestman_rc_path, old_port, new_port, backup=False)
        old_gridmap = 'GridMapFileName=/etc/bestman2/conf/grid-mapfile.empty'
        new_gridmap = 'GridMapFileName=/etc/grid-security/grid-mapfile'
        files.replace(bestman_rc_path, old_gridmap, new_gridmap, backup=False)
        files.replace(bestman_rc_path, 'eventLogLevel=INFO', 'eventLogLevel=DEBUG', backup=False)
        core.system(('cat', bestman_rc_path))

        env_file = '/etc/sysconfig/bestman2'
        old_auth = 'BESTMAN_GUMS_ENABLED=yes'
        new_auth = 'BESTMAN_GUMS_ENABLED=no'
        files.replace(env_file, old_auth, new_auth, backup=False)

        log4j_path = '/etc/bestman2/properties/log4j.properties'
        log4j_contents = files.read(log4j_path, as_single_string=True)
        log4j_contents = log4j_contents.replace('FATAL', 'INFO')
        files.write(log4j_path, log4j_contents, backup=False)

    @osgrelease(3.3)
    def test_05_start_bestman(self):
        core.config['bestman.pid-file'] = '/var/run/bestman2.pid'
        core.state['bestman.started-server'] = False
        core.state['bestman.server-running'] = False

        core.skip_ok_unless_installed('bestman2-server', 'bestman2-client', 'gums-service')
        if service.is_running('bestman2'):
            core.state['bestman.server-running'] = True
            self.skip_ok('bestman2 already running')

        # Dump the bestman logs into the test logs for debugging
        def _dump_logfiles():
            logdir = '/var/log/bestman2'
            for logfile in ('bestman2.log', 'event.srm.log'):
                core.system(('cat', os.path.join(logdir, logfile)))

        try:
            service.check_start('bestman2')
        except AssertionError:
            _dump_logfiles()
            raise
        core.state['bestman.started-server'] = True
        core.state['bestman.server-running'] = True
