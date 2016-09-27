import cagen
import os

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.tomcat as tomcat
import osgtest.library.voms as voms
import osgtest.library.osgunittest as osgunittest

class TestStartVOMS(osgunittest.OSGTestCase):

    def test_01_config_certs(self):
        core.config['certs.httpcert'] = '/etc/grid-security/http/httpcert.pem'
        core.config['certs.httpkey'] = '/etc/grid-security/http/httpkey.pem'
        core.config['certs.vomscert'] = '/etc/grid-security/voms/vomscert.pem'
        core.config['certs.vomskey'] = '/etc/grid-security/voms/vomskey.pem'

    def test_02_install_voms_certs(self):
        voms.skip_ok_unless_installed()
        vomscert = core.config['certs.vomscert']
        vomskey = core.config['certs.vomskey']
        self.skip_ok_if(core.check_file_and_perms(vomscert, 'voms', 0644) and
                        core.check_file_and_perms(vomskey, 'voms', 0400),
                        'VOMS cert exists and has proper permissions')
        core.install_cert('certs.vomscert', 'certs.hostcert', 'voms', 0644)
        core.install_cert('certs.vomskey', 'certs.hostkey', 'voms', 0400)

    def test_03_install_http_certs(self):
        core.skip_ok_unless_installed('voms-admin-server')
        httpcert = core.config['certs.httpcert']
        httpkey = core.config['certs.httpkey']
        self.skip_ok_if(core.check_file_and_perms(httpcert, 'tomcat', 0644) and
                        core.check_file_and_perms(httpkey, 'tomcat', 0400),
                        'HTTP cert exists and has proper permissions')
        core.install_cert('certs.httpcert', 'certs.hostcert', 'tomcat', 0644)
        core.install_cert('certs.httpkey', 'certs.hostkey', 'tomcat', 0400)

    def test_04_config_voms(self):
        core.config['voms.vo'] = 'osgtestvo'
        core.config['voms.lock-file'] = '/var/lock/subsys/voms.osgtestvo'
        core.config['voms.vo-webapp'] = os.path.join(
            tomcat.datadir(), "conf/Catalina/localhost/voms#osgtestvo.xml")
        core.config['voms.webapp-log'] = os.path.join(
            tomcat.logdir(), 'voms-admin-osgtestvo.log')
        # The DB created by voms-admin would have the user 'admin-osgtestvo',
        # but the voms_install_db script provided by voms-server does not
        # like usernames with '-' in them.
        core.config['voms.dbusername'] = 'voms_' + core.config['voms.vo']

    def test_05_create_vo(self):
        voms.skip_ok_unless_installed()

        use_voms_admin = core.rpm_is_installed('voms-admin-server')
        voms.create_vo(vo=core.config['voms.vo'],
                       dbusername=core.config['voms.dbusername'],
                       dbpassword='secret',
                       vomscert=core.config['certs.vomscert'],
                       vomskey=core.config['certs.vomskey'],
                       use_voms_admin=use_voms_admin)

    def test_06_add_local_admin(self):
        core.skip_ok_unless_installed('voms-admin-server', 'voms-mysql-plugin')
        host_dn, host_issuer = \
            cagen.certificate_info(core.config['certs.hostcert'])
        command = ('voms-db-deploy.py', 'add-admin',
                   '--vo', core.config['voms.vo'],
                   '--dn', host_dn, '--ca', host_issuer)
        core.check_system(command, 'Add VO admin')

    def test_07_config_va_properties(self):
        core.skip_ok_unless_installed('voms-admin-server')

        path = os.path.join('/etc/voms-admin', core.config['voms.vo'],
                            'voms.service.properties')
        contents = files.read(path)

        had_csrf_line = False
        for line in contents:
            if 'voms.csrf.log_only' in line:
                line = 'voms.csrf.log_only = true\n'
                had_csrf_line = True
            elif line[-1] != '\n':
                line = line + '\n'
        if not had_csrf_line:
            contents += 'voms.csrf.log_only = true\n'

        files.write(path, contents, backup=False)

    def test_08_advertise(self):
        voms.skip_ok_unless_installed()

        voms.advertise_lsc(core.config['voms.vo'], core.config['certs.hostcert'])
        files.preserve('/etc/vomses', owner='voms')
        voms.advertise_vomses(core.config['voms.vo'], core.config['certs.hostcert'])

        core.system('ls -ldF /etc/*vom*', shell=True)
        core.system(('find', '/etc/grid-security/vomsdir', '-ls'))

    def test_09_start_voms(self):
        core.state['voms.started-server'] = False

        voms.skip_ok_unless_installed()
        self.skip_ok_if(os.path.exists(core.config['voms.lock-file']), 'apparently running')

        if core.el_release() < 7:
            core.config['voms_service'] = 'voms'
        else:
            core.config['voms_service'] = 'voms@' + core.config['voms.vo']

        service.start(core.config['voms_service'])
        self.assert_(service.is_running(core.config['voms_service']), 'VOMS failed to start')

        core.state['voms.started-server'] = True

    def test_10_install_vo_webapp(self):
        core.state['voms.installed-vo-webapp'] = False
        core.skip_ok_unless_installed('voms-admin-server')
        self.skip_ok_if(os.path.exists(core.config['voms.vo-webapp']), 'apparently installed')

        service.start('voms-admin')
        self.assert_(service.is_running('voms-admin'), 'VOMS admin failed to start')
        core.state['voms.installed-vo-webapp'] = True
