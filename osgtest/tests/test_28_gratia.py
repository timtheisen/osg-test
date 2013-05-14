import os
import pwd
import shutil
import socket
import stat
import osgtest.library.core as core
import osgtest.library.tomcat as tomcat
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStartGratia(osgunittest.OSGTestCase):

#===============================================================================
# check_file_and_perms has been taken from test_20_voms.py
# We should consider putting this code in the core library
#===============================================================================
 
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


#===============================================================================
# install_cert has been taken from test_20_voms.py
# We should consider putting this code in the core library
#===============================================================================
    #===========================================================================
    # Carefully install a certificate with the given key from the given
    # source path, then set ownership and permissions as given.  Record
    # each directory and file created by this process into the config
    # dictionary; do so immediately after creation, so that the
    # remove_cert() function knows exactly what to remove/restore.
    #===========================================================================
    def install_cert(self, target_key, source_key, owner_name, permissions):
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

    # ==================================================================
    
    #===========================================================================
    # This helper method loops through the passed in infile line by line. 
    # If it finds the passed in pattern, it replaces the whole line with
    # the passed in full_line.
    #===========================================================================
    
    def patternreplace(self, infile_name, pattern, full_line):
        infile = open(infile_name, "r")
        outfile_name = infile_name + ".tmp"
        outfile = file(outfile_name, 'w')
        
        for line in infile:
            if pattern in line:
                line = full_line + "\n"
            outfile.writelines(line)
        
        shutil.move(outfile_name, infile_name)
        
    #=======================================================================
    # This is taken from the trunk core.py. Need to figure out how to import...
    #=======================================================================
    def get_package_envra(self, package_name):
        """Query and return the ENVRA (Epoch, Name, Version, Release, Arch) of an
        installed package as a tuple. Can raise OSError if rpm does not return
        output in the right format.
    
        """
        command = ('rpm', '--query', package_name, '--queryformat=%{EPOCH} %{NAME} %{VERSION} %{RELEASE} %{ARCH}')
        status, stdout, stderr = core.system(command)
        # Not checking stderr because signature warnings get written there and
        # we do not care about those.
        if (status != 0) or (stdout is None):
            raise OSError(status, stdout)
    
        envra = stdout.strip().split(' ')
        if len(envra) != 5:
            raise OSError(status, stdout)
        (epoch, name, version, release, arch) = envra
        return (epoch, name, version, release, arch)
   

    #===========================================================================
    # This test modifies "/etc/gratia/collector/service-authorization.properties" file
    #===========================================================================
      
    def test_01_service_authorization(self):
        core.skip_ok_unless_installed('gratia-service')
        
        # The name of the gratia directory changed
        gratia_version = self.get_package_envra('gratia-service')[2]
        print gratia_version
        gratia_version_split = gratia_version.split('.')
        print gratia_version_split
        if gratia_version_split >= ['1', '13', '5']:
            core.config['gratia.directory'] = "services"
        else:
            core.config['gratia.directory'] = "collector"
            
        gratia_auth = "/etc/gratia/" + core.config['gratia.directory'] + "/service-authorization.properties"
        self.patternreplace(gratia_auth, "service.mysql.rootpassword", "service.mysql.rootpassword=admin")
        self.patternreplace(gratia_auth, "service.mysql.user", "service.mysql.user=gratia")
        self.patternreplace(gratia_auth, "service.mysql.password", "service.mysql.password=password")
        
    #===========================================================================
    # This test modifies "/etc/gratia/collector/service-configuration.properties" file
    #===========================================================================
        
    def test_02_service_configuration(self):
        core.skip_ok_unless_installed('gratia-service')
        gratia_conf = "/etc/gratia/" + core.config['gratia.directory'] + "/service-configuration.properties"
        host = socket.gethostname()
        mysqlurl="service.mysql.url=jdbc:mysql://" +  host + ":3306/gratia"
        self.patternreplace(gratia_conf, "service.mysql.url", mysqlurl)
        openconn="service.open.connection=http://" + host + ":8880"
        self.patternreplace(gratia_conf, "service.open.connection", openconn)
        secureconn="service.secure.connection=https://" + host + ":8443"
        self.patternreplace(gratia_conf, "service.secure.connection", secureconn)
    
    #===========================================================================
    # This test executes the install-database command
    #===========================================================================
    def test_03_install_database(self):
        core.skip_ok_unless_installed('gratia-service')    
        command = ('/usr/share/gratia/install-database',)
        core.check_system(command, 'Unable to install Gratia Database !')
        
    #===========================================================================
    # This test sets certificates related parameters
    #===========================================================================
    def test_04_config_certs(self):
        core.config['certs.hostcert'] = '/etc/grid-security/hostcert.pem'
        core.config['certs.hostkey'] = '/etc/grid-security/hostkey.pem'
        core.config['certs.httpcert'] = '/etc/grid-security/http/httpcert.pem'
        core.config['certs.httpkey'] = '/etc/grid-security/http/httpkey.pem'

    #===========================================================================
    # This test sets installs http certificates
    #===========================================================================
    def test_05_install_http_certs(self):
        core.skip_ok_unless_installed('gratia-service')
        httpcert = core.config['certs.httpcert']
        httpkey = core.config['certs.httpkey']
        self.skip_ok_if(self.check_file_and_perms(httpcert, 'tomcat', 0644) and
                        self.check_file_and_perms(httpkey, 'tomcat', 0400),
                        'HTTP cert exists and has proper permissions')
        self.install_cert('certs.httpcert', 'certs.hostcert', 'tomcat', 0644)
        self.install_cert('certs.httpkey', 'certs.hostkey', 'tomcat', 0400)
        
    #===========================================================================
    # This test stops the Tomcat service
    #===========================================================================
    def test_06_stop_tomcat(self):
        core.skip_ok_unless_installed(tomcat.pkgname())
        service.stop('tomcat')

    #===========================================================================
    # This test configures Tomcat
    #===========================================================================
    def test_07_configure_tomcat(self):
        core.skip_ok_unless_installed('gratia-service')
        command = ('/usr/share/gratia/configure_tomcat',)
        core.check_system(command, 'Unable to configure Tomcat !')

    #===========================================================================
    # This test starts the Tomcat service
    #===========================================================================
    def test_08_start_tomcat(self):
        core.skip_ok_unless_installed(tomcat.pkgname())
        service.start('tomcat', init_script=tomcat.pkgname(), sentinel_file=tomcat.pidfile())
   
