import os
import pwd
import shutil
import socket
import stat
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.tomcat as tomcat
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStartGratia(osgunittest.OSGTestCase):

    def check_file_and_perms(self, file_path, owner_name, permissions):
        """Return True if the file at 'file_path' exists, is owned by
        'owner_name', is a file, and has the given permissions; False otherwise
 
        """
        owner_uid = pwd.getpwnam(owner_name)
        try:
            file_stat = os.stat(file_path)
            return (file_stat.st_uid == owner_uid and
                    file_stat.st_mode & 07777 == permissions and
                    stat.S_ISREG(file_stat.st_mode))
        except OSError: # file does not exist
            return False

    def install_cert(self, target_key, source_key, owner_name, permissions):
        """Install_cert has been taken from test_20_voms.py  We should consider putting this code in the core library.
     Carefully install a certificate with the given key from the given
     source path, then set ownership and permissions as given.  Record
     each directory and file created by this process into the config
     dictionary; do so immediately after creation, so that the
     remove_cert() function knows exactly what to remove/restore."""

        target_path = core.config[target_key]
        target_dir = os.path.dirname(target_path)
        source_path = core.config[source_key]
        user = pwd.getpwnam(owner_name)
 
        # Using os.path.lexists because os.path.exists return False for broken symlinks
        if os.path.lexists(target_path):
            backup_path = target_path + '.osgtest.backup'
            shutil.move(target_path, backup_path)
            core.state[target_key + '-backup'] = backup_path
 
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            core.state[target_key + '-dir'] = target_dir
            os.chown(target_dir, user.pw_uid, user.pw_gid)
            os.chmod(target_dir, 0755)
 
        shutil.copy(source_path, target_path)
        core.state[target_key] = target_path
        os.chown(target_path, user.pw_uid, user.pw_gid)
        os.chmod(target_path, permissions)

    
    def patternreplace(self, infile_name, pattern, full_line):
        """This helper method loops through the passed in infile line by line. 
     If it finds the passed in pattern, it replaces the whole line with
     the passed in full_line."""

        infile = open(infile_name, "r")
        outfile_name = infile_name + ".tmp"
        outfile = file(outfile_name, 'w')
        
        #If the pattern is found in a non-comment line, replace the line with the passed in "full_line"
        for line in infile:
            if pattern in line and not line.startswith('#'):
                line = full_line + "\n"
            outfile.writelines(line)
        
        shutil.move(outfile_name, infile_name)
        

    def tuple_cmp (self, t1, t2):
        """ This tuple comparsion method assumes: 
     A. Tuple has 3 entries 
     B. An integer comparsion is desired
     Note that the python "cmp" method does NOT perform integer comparison
     Similar to python "cmp" method, 
     The return value is negative if t1 < t2, zero if t1 == t2 and strictly positive if t1 > t2."""

        t1_0 = int(t1[0])
        t1_1 = int(t1[1])
        t1_2 = int(t1[2])
        
        t2_0 = int(t2[0])
        t2_1 = int(t2[1])
        t2_2 = int(t2[2])
        
        if (t1_0 < t2_0):
            return -1
        elif (t1_0  > t2_0):
            return 1
        else: #t1_0 == t2_0
            if (t1_1 < t2_1):
                return -1
            elif (t1_1 > t2_1):
                return 1
            else: #t1_1 == t2_1
                if (t1_2 < t2_2):
                    return -1
                elif (t1_2  > t2_2):
                    return 1
                else: #t1_2 == t2_2
                    return 0
        
    #This test sets gratia-directory + certificates related parameters
    def test_01_config_parameters(self):
        core.skip_ok_unless_installed('gratia-service')
        core.config['gratia.host']= core.get_hostname()
        core.config['gratia.config.dir'] = '/etc/gratia'
        # The name of the gratia directory changed
        gratia_version = core.get_package_envra('gratia-service')[2]
        gratia_version_split = gratia_version.split('.')
        
        if (self.tuple_cmp(gratia_version_split, ['1', '13', '5']) < 0):
            core.config['gratia.directory'] = "collector"
        else:
            core.config['gratia.directory'] = "services"
            
        core.config['certs.hostcert'] = '/etc/grid-security/hostcert.pem'
        core.config['certs.hostkey'] = '/etc/grid-security/hostkey.pem'
        core.config['certs.httpcert'] = '/etc/grid-security/http/httpcert.pem'
        core.config['certs.httpkey'] = '/etc/grid-security/http/httpkey.pem'
        
        filename = "/tmp/gratia_reader_pass." + str(os.getpid()) + ".txt"
        contents="[client]\n" + "password=reader\n"
        files.write(filename, contents, backup=False)
        core.config['gratia.sql.file'] = filename
        core.config['gratia.sql.querystring'] = "\" | mysql --defaults-extra-file=\"" + core.config['gratia.sql.file'] + "\" --skip-column-names -B --unbuffered  --user=reader --port=3306"
        core.config['gratia.tmpdir.prefix'] = "/var/lib/gratia/tmp/gratiafiles/"
        core.config['gratia.tmpdir.postfix'] = "_" + core.config['gratia.host'] + "_" + core.config['gratia.host'] + "_8880"
        core.config['gratia.log.file'] = "/var/log/gratia-service/gratia.log"
        core.state['gratia.log.stat'] = None
      
      
    #This test modifies "/etc/gratia/collector/service-authorization.properties" file
    def test_02_service_authorization(self):
        core.skip_ok_unless_installed('gratia-service')
        gratia_auth = core.config['gratia.config.dir'] + "/" + core.config['gratia.directory'] + "/service-authorization.properties"
        self.patternreplace(gratia_auth, "service.mysql.rootpassword", "service.mysql.rootpassword=")
        self.patternreplace(gratia_auth, "service.mysql.user", "service.mysql.user=gratia")
        self.patternreplace(gratia_auth, "service.mysql.password", "service.mysql.password=password")
        
        
    #This test modifies "/etc/gratia/collector/service-configuration.properties" file
    def test_03_service_configuration(self):
        core.skip_ok_unless_installed('gratia-service')
        gratia_conf = core.config['gratia.config.dir'] + "/" + core.config['gratia.directory'] + "/service-configuration.properties"
        mysqlurl="service.mysql.url=jdbc:mysql://" +  core.config['gratia.host'] + ":3306/gratia"
        self.patternreplace(gratia_conf, "service.mysql.url", mysqlurl)
        openconn="service.open.connection=http://" + core.config['gratia.host'] + ":8880"
        self.patternreplace(gratia_conf, "service.open.connection", openconn)
        secureconn="service.secure.connection=https://" + core.config['gratia.host'] + ":8443"
        self.patternreplace(gratia_conf, "service.secure.connection", secureconn)
        #Changing the log level to capture Probe related messages, needed later
        self.patternreplace(gratia_conf, "service.service.level=", "service.service.level=FINE")
    
    #This test executes the install-database command
    def test_04_install_database(self):
        core.state['gratia.database-installed'] = False
        core.skip_ok_unless_installed('gratia-service')    
        command = ('/usr/share/gratia/install-database',)
        core.check_system(command, 'Unable to install Gratia Database !')
        core.state['gratia.database-installed'] = True

    #This test sets installs http certificates
    def test_05_install_http_certs(self):
        core.skip_ok_unless_installed('gratia-service')
        httpcert = core.config['certs.httpcert']
        httpkey = core.config['certs.httpkey']
        self.skip_ok_if(self.check_file_and_perms(httpcert, 'tomcat', 0644) and
                        self.check_file_and_perms(httpkey, 'tomcat', 0400),
                        'HTTP cert exists and has proper permissions')
        self.install_cert('certs.httpcert', 'certs.hostcert', 'tomcat', 0644)
        self.install_cert('certs.httpkey', 'certs.hostkey', 'tomcat', 0400)
        
    #This test stops the Tomcat service
    def test_06_stop_tomcat(self):
        core.skip_ok_unless_installed('gratia-service')    
        core.skip_ok_unless_installed(tomcat.pkgname())
        service.stop('tomcat')

    #This test configures Tomcat
    def test_07_configure_tomcat(self):
        core.skip_ok_unless_installed('gratia-service')
        command = ('/usr/share/gratia/configure_tomcat',)
        core.check_system(command, 'Unable to configure Tomcat !')

    #This test starts the Tomcat service
    def test_08_start_tomcat(self):
        core.skip_ok_unless_installed('gratia-service')
        core.skip_ok_unless_installed(tomcat.pkgname())
        service.start('tomcat', init_script=tomcat.pkgname(), sentinel_file=tomcat.pidfile())
   
