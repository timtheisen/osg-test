import cagen
import os

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.voms as voms
import osgtest.library.osgunittest as osgunittest

class TestStartVOMS(osgunittest.OSGTestCase):

    def test_01_config_certs(self):
        core.config['certs.vomscert'] = '/etc/grid-security/voms/vomscert.pem'
        core.config['certs.vomskey'] = '/etc/grid-security/voms/vomskey.pem'

    def test_02_install_voms_certs(self):
        voms.skip_ok_unless_server_is_installed()
        # ^^ we use the host cert, not the voms cert for voms-proxy-direct
        vomscert = core.config['certs.vomscert']
        vomskey = core.config['certs.vomskey']
        self.skip_ok_if(core.check_file_and_perms(vomscert, 'voms', 0o644) and
                        core.check_file_and_perms(vomskey, 'voms', 0o400),
                        'VOMS cert exists and has proper permissions')
        core.install_cert('certs.vomscert', 'certs.hostcert', 'voms', 0o644)
        core.install_cert('certs.vomskey', 'certs.hostkey', 'voms', 0o400)

    def test_04_config_voms(self):
        core.config['voms.vo'] = voms.VONAME
        core.config['voms.lock-file'] = '/var/lock/subsys/voms.osgtestvo'
        # The DB created by voms-admin would have the user 'admin-osgtestvo',
        # but the voms_install_db script provided by voms-server does not
        # like usernames with '-' in them.
        core.config['voms.dbusername'] = 'voms_' + core.config['voms.vo']

    def test_05_create_vo(self):
        voms.skip_ok_unless_server_is_installed()

        # Destroy the DB if it already exists
        try:
            voms.destroy_db(core.config['voms.vo'], core.config['voms.dbusername'])
            voms.destroy_voms_conf(core.config['voms.vo'])
        except (EnvironmentError, AssertionError):
            pass

        voms.create_vo(vo=core.config['voms.vo'],
                       dbusername=core.config['voms.dbusername'],
                       dbpassword='secret',
                       vomscert=core.config['certs.vomscert'],
                       vomskey=core.config['certs.vomskey'])

    def test_08_advertise(self):
        voms.skip_ok_unless_can_make_proxy()

        voms.advertise_lsc(core.config['voms.vo'], core.config['certs.hostcert'])
        files.preserve('/etc/vomses', owner='voms')
        voms.advertise_vomses(core.config['voms.vo'], core.config['certs.hostcert'])

        core.system('ls -ldF /etc/*vom*', shell=True)
        core.system(('find', '/etc/grid-security/vomsdir', '-ls'))

    def test_09_start_voms(self):
        core.state['voms.started-server'] = False

        voms.skip_ok_unless_server_is_installed()
        self.skip_ok_if(os.path.exists(core.config['voms.lock-file']), 'apparently running')

        if core.el_release() < 7:
            core.config['voms_service'] = 'voms'
        else:
            core.config['voms_service'] = 'voms@' + core.config['voms.vo']

        service.check_start(core.config['voms_service'])

        core.state['voms.started-server'] = True
