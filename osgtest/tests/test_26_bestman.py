import os
import osgtest.library.core as core
import osgtest.library.files as files
import pwd
import shutil
import unittest

class TestStartBestman(unittest.TestCase):

    def install_cert(self, target_key, source_key, owner_name, permissions):
        target_path = core.config[target_key]
        target_dir = os.path.dirname(target_path)
        source_path = core.config[source_key]
        user = pwd.getpwnam(owner_name)

        if os.path.exists(target_path):
            backup_path = target_path + '.osgtest.backup'
            shutil.move(target_path, backup_path)
            core.state[target_key + '-backup'] = backup_path

        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
            core.state[target_key + '-dir'] = target_dir
            os.chown(target_dir, user.pw_uid, user.pw_gid)
            os.chmod(target_dir, 0755)

        shutil.copy(source_path, target_path)
        core.state[target_key] = target_path
        os.chown(target_path, user.pw_uid, user.pw_gid)
        os.chmod(target_path, permissions)

    def test_01_config_certs(self):
        core.config['certs.hostcert'] = '/etc/grid-security/hostcert.pem'
        core.config['certs.hostkey'] = '/etc/grid-security/hostkey.pem'
        core.config['certs.httpcert'] = '/etc/grid-security/http/httpcert.pem'
        core.config['certs.httpkey'] = '/etc/grid-security/http/httpkey.pem'
	core.config['certs.bestmancert'] = '/etc/grid-security/bestman/bestmancert.pem'
        core.config['certs.bestmankey'] = '/etc/grid-security/bestman/bestmankey.pem'	

    def test_02_install_bestman_certs(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client', 'voms-clients'):
            core.skip('Bestman not installed')
            return
        if (os.path.exists(core.config['certs.bestmancert']) and
            os.path.exists(core.config['certs.bestmankey'])):
            return
        self.install_cert('certs.bestmancert', 'certs.hostcert', 'bestman', 0644)
        self.install_cert('certs.bestmankey', 'certs.hostkey', 'bestman', 0400)

    def test_03_modify_sudoers(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client', 'voms-clients'):
           core.skip('Bestman not installed')
           return
        orig_file = '/etc/sudoers'
        contents = files.read(orig_file)
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
           files.write(orig_file, new_contents)

    def test_04_modify_bestman_conf(self):
        if core.missing_rpm('bestman2-server', 'bestman2-client', 'voms-clients'):
           core.skip('Bestman not installed')
           return
        config_file = '/etc/bestman2/conf/bestman2.rc'
	env_file = '/etc/sysconfig/bestman2'
        old_port = 'securePort=8443'
        new_port = 'securePort=10443'
        old_gridmap = 'GridMapFileName=/etc/bestman2/conf/grid-mapfile.empty'
        new_gridmap = 'GridMapFileName=/etc/grid-security/grid-mapfile'
	old_auth = 'BESTMAN_GUMS_ENABLED=yes'
	new_auth = 'BESTMAN_GUMS_ENABLED=no'
	files.replace(config_file,old_port,new_port)
	files.replace(config_file,old_gridmap,new_gridmap)
	files.replace(env_file,old_auth,new_auth)
    
    def test_05_start_bestman(self):
        core.config['bestman.pid-file'] = '/var/run/bestman2.pid'
        core.state['bestman.started-server'] = False

        if core.missing_rpm('bestman2-server', 'bestman2-client', 'voms-clients'):
            core.skip('not installed')
            return
        if os.path.exists(core.config['bestman.pid-file']):
            core.skip('apparently running')
            return

        command = ('service', 'bestman2', 'start')
        stdout, _, fail = core.check_system(command, 'Starting bestman2')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(os.path.exists(core.config['bestman.pid-file']),
                     'Bestman server PID file missing')
        core.state['bestman.started-server'] = True
