import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import os
import re
from distutils.sysconfig import get_python_libs
import shutil


class TestGratia(osgunittest.OSGTestCase):
    
    def patternreplace(self, infile_name, pattern, full_line):
        infile = open(infile_name, "r")
        outfile_name = infile_name + ".tmp"
        outfile = file(outfile_name, 'w')
        
        for line in infile:
            if pattern in line:
                line = full_line + "\n"
            outfile.writelines(line)
        
        shutil.move(outfile_name, infile_name)

    def test_01_gratia_admin_webpage (self):
         
        core.skip_ok_unless_installed('gratia-service')
        command = ('curl', 'http://fermicloud316.fnal.gov:8880/gratia-administration/status.html?wantDetails=0')
        status, stdout, stderr = core.system(command)
        #print "stdout is: " + str(stdout)
        #print "stderr is: " + str(stderr)
        self.assertEqual(status, 0, 'Unable to launch gratia admin webpage')
        
    def test_02_show_databases(self):
        core.skip_ok_unless_installed('gratia-service')    
       
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        #print filename
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        
        #Command to show the databases is:
        #echo "show databases;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" -B --unbuffered  --user=root --port=3306         
        command = "echo \"show databases;\" | mysql --defaults-extra-file=\"" + filename + "\" -B --unbuffered  --user=root --port=3306 | wc -l",
        status, stdout, stderr = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to install Gratia Database !')
        #self.assertEqual(stdout, 5, 'Incorrect total number of databases !')
        print "show_databases stdout is: " + stdout
        result = re.search('5', stdout, re.IGNORECASE)
        self.assert_(result is not None)
        os.remove(filename)
        
    def test_03_show_gratia_database_tables(self):
        core.skip_ok_unless_installed('gratia-service')    
       
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        #print filename
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        
        #Command to show the tabes in the gratia database is:
        #echo "use gratia;show tables;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" -B --unbuffered  --user=root --port=3306         
        command = "echo \"use gratia;show tables;\" | mysql --defaults-extra-file=\"" + filename + "\" -B --unbuffered  --user=root --port=3306 | wc -l",
        status, stdout, stderr = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to install Gratia Database !')
        #self.assertEqual(stdout, 5, 'Incorrect total number of databases !')
        print "show_gratia_database_tables stdout is: " + stdout
        result = re.search('82', stdout, re.IGNORECASE)
        self.assert_(result is not None)
        os.remove(filename)
        
    def test_04_modify_gridftptransfer_probeconfig(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        probeconfig = "/etc/gratia/gridftp-transfer/ProbeConfig"
        self.patternreplace(probeconfig, "CollectorHost", "CollectorHost=\"fermicloud316.fnal.gov:8880\"")
        self.patternreplace(probeconfig, "SSLHost", "SSLHost=\"fermicloud316.fnal.gov:8443\"")
        self.patternreplace(probeconfig, "SSLRegistrationHost", "SSLRegistrationHost=\"fermicloud316.fnal.gov:8880\"")
        self.patternreplace(probeconfig, "SiteName", "SiteName=\"OSG Test site\"")
        self.patternreplace(probeconfig, "SiteName", "EnableProbe=\"1\"")
        
    def test_05_copy_gridftp_logs(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        grid_ftp_log = os.path.join(get_python_lib(), 'files', 'gridftp.log')
        grid_ftp_auth_log = os.path.join(get_python_lib(), 'files', 'gridftp-auth.log')
        dst_dir = '/var/log'
        shutil.copyfile(grid_ftp_log, dst_dir)
        shutil.copyfile(grid_ftp_auth_log, dst_dir)
        print("test_05_copy_gridftp_logs - content of /var/log:\n" + os.listdir('/var/log'))
    
    def test_06_execute_gridftptransfer_probedriver(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        command = ('/usr/share/gratia/gridftp-transfer/GridftpTransferProbeDriver',)
        status, stdout, stderr = core.system(command)
        self.assertEqual(status, 0, 'Unable to execute GridftpTransferProbeDriver!')
        self.assert_(not os.listdir('/var/lib/gratia/tmp/gratiafiles/subdir.gridftp-transfer_fermicloud316.fnal.gov_fermicloud316.fnal.gov_8880/outbox/'), 'gridftp-transfer outbox NOT empty !')
        core.state['gratia.gridftp-transfer-running'] = True
        
    def test_07_checkdatabase_gridftptransfer_probedriver(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        self.skip_bad_if(core.state['gratia.gridftp-transfer-running'] == False)
        pass

        

        
        