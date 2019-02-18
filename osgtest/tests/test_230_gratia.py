import os
import shutil

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.tomcat as tomcat

class TestStartGratia(osgunittest.OSGTestCase):

    @core.elrelease(6)
    def setUp(self):
        pass

    def patternreplace(self, infile_name, pattern, full_line):
        """This helper method loops through the passed in infile line by line.
     If it finds the passed in pattern, it replaces the whole line with
     the passed in full_line."""

        infile = open(infile_name, "r")
        outfile_name = infile_name + ".tmp"
        outfile = open(outfile_name, 'w')

        #If the pattern is found in a non-comment line, replace the line with the passed in "full_line"
        for line in infile:
            if pattern in line and not line.startswith('#'):
                line = full_line + "\n"
            outfile.writelines(line)

        shutil.move(outfile_name, infile_name)


    #This test preserves the mentioned gratia directory, if it exists
    def test_01_backup_varlibgratia(self):
        core.skip_ok_unless_installed('gratia-service')
        if os.path.exists('/var/lib/gratia'):
            command = ("cp -pr /var/lib/gratia /var/lib/gratia_production",)
            core.check_system(command, 'Could not backup /var/lib/gratia', shell=True)
            core.state['gratia.varlibgratia-backedup'] = True

    #This test preserves the mentioned gratia directory, if it exists
    def test_02_backup_varlibgratiaservice(self):
        core.skip_ok_unless_installed('gratia-service')
        if os.path.exists('/var/lib/gratia-service'):
            command = ("cp -pr /var/lib/gratia-service /var/lib/gratia-service_production",)
            core.check_system(command, 'Could not backup /var/lib/gratia-service', shell=True)
            core.state['gratia.varlibgratia-service-backedup'] = True

    #This test sets gratia-directory + certificates related parameters
    def test_03_config_parameters(self):
        core.skip_ok_unless_installed('gratia-service')
        core.config['gratia.host'] = core.get_hostname()
        core.config['gratia.config.dir'] = '/etc/gratia'
        # The name of the gratia directory changed
        if core.PackageVersion('gratia-service') < '1.13.5':
            core.config['gratia.directory'] = "collector"
        else:
            core.config['gratia.directory'] = "services"

        core.config['certs.httpcert'] = '/etc/grid-security/http/httpcert.pem'
        core.config['certs.httpkey'] = '/etc/grid-security/http/httpkey.pem'

        filename = "/tmp/gratia_reader_pass." + str(os.getpid()) + ".txt"
        contents = "[client]\n" + "password=reader\n"
        files.write(filename, contents, backup=False)
        core.config['gratia.sql.file'] = filename
        core.config['gratia.sql.querystring'] = "\" | mysql --defaults-extra-file=\"" + core.config['gratia.sql.file'] + "\" --skip-column-names -B --unbuffered  --user=reader --port=3306"
        core.config['gratia.tmpdir.prefix'] = "/var/lib/gratia/tmp/gratiafiles/"
        core.config['gratia.tmpdir.postfix'] = "_" + core.config['gratia.host'] + "_" + core.config['gratia.host'] + "_8880"
        core.config['gratia.log.file'] = "/var/log/gratia-service/gratia.log"
        core.state['gratia.log.stat'] = None

    #This test preserves the mentioned gratia directory, if it exists
    def test_04_backup_etcgratia_collector_or_services(self):
        core.skip_ok_unless_installed('gratia-service')
        gratia_directory_to_preserve = core.config['gratia.config.dir'] + "/" + core.config['gratia.directory']
        if os.path.exists(gratia_directory_to_preserve):
            backup_path = gratia_directory_to_preserve + '_production'
            command = ("cp -pr " + gratia_directory_to_preserve + " " + backup_path,)
            core.check_system(command, 'Could not backup ' + gratia_directory_to_preserve, shell=True)
            core.state['gratia.etcgratia_collector_or_services-backedup'] = gratia_directory_to_preserve

    #This test modifies "/etc/gratia/collector/service-authorization.properties" file
    def test_05_service_authorization(self):
        core.skip_ok_unless_installed('gratia-service')
        gratia_auth = core.config['gratia.config.dir'] + "/" + core.config['gratia.directory'] + "/service-authorization.properties"
        self.patternreplace(gratia_auth, "service.mysql.rootpassword", "service.mysql.rootpassword=")
        self.patternreplace(gratia_auth, "service.mysql.user", "service.mysql.user=gratia")
        self.patternreplace(gratia_auth, "service.mysql.password", "service.mysql.password=password")

    #This test modifies "/etc/gratia/collector/service-configuration.properties" file
    def test_06_service_configuration(self):
        core.skip_ok_unless_installed('gratia-service')
        gratia_conf = core.config['gratia.config.dir'] + "/" + core.config['gratia.directory'] + "/service-configuration.properties"
        mysqlurl = "service.mysql.url=jdbc:mysql://" +  core.config['gratia.host'] + ":3306/gratia_osgtest"
        self.patternreplace(gratia_conf, "service.mysql.url", mysqlurl)
        openconn = "service.open.connection=http://" + core.config['gratia.host'] + ":8880"
        self.patternreplace(gratia_conf, "service.open.connection", openconn)
        secureconn = "service.secure.connection=https://" + core.config['gratia.host'] + ":8443"
        self.patternreplace(gratia_conf, "service.secure.connection", secureconn)
        #Changing the log level to capture Probe related messages, needed later
        self.patternreplace(gratia_conf, "service.service.level=", "service.service.level=FINE")

    #This test executes the install-database command
    def test_07_install_database(self):
        core.state['gratia.database-installed'] = False
        core.skip_ok_unless_installed('gratia-service')
        command = ('/usr/share/gratia/install-database',)
        core.check_system(command, 'Unable to install Gratia Database.')
        core.state['gratia.database-installed'] = True

    #This test sets installs http certificates
    def test_08_install_http_certs(self):
        core.skip_ok_unless_installed('gratia-service')
        httpcert = core.config['certs.httpcert']
        httpkey = core.config['certs.httpkey']
        self.skip_ok_if(core.check_file_and_perms(httpcert, 'tomcat', 0o644) and
                        core.check_file_and_perms(httpkey, 'tomcat', 0o400),
                        'HTTP cert exists and has proper permissions')
        core.install_cert('certs.httpcert', 'certs.hostcert', 'tomcat', 0o644)
        core.install_cert('certs.httpkey', 'certs.hostkey', 'tomcat', 0o400)

    def test_09_config_user_vo_map(self):
        core.skip_ok_unless_installed('gratia-service')
        user_vo_map_file = '/var/lib/osg/user-vo-map'
        core.config['gratia.user-vo-map'] = user_vo_map_file
        conFileContents = files.read('/usr/share/osg-test/gratia/user-vo-map')
        if files.filesBackedup(user_vo_map_file, 'root'):
            files.write(core.config['gratia.user-vo-map'],
                        conFileContents,
                        backup=False)
        else:
            files.write(core.config['gratia.user-vo-map'],
                        conFileContents,
                        owner='root')
