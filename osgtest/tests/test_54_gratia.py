import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import os
import re
from distutils.sysconfig import get_python_lib
import shutil
import socket
import time


class TestGratia(osgunittest.OSGTestCase):
    
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

    #===============================================================================
    # This test tries to launch a gratia admin webpage
    #===============================================================================
    def test_01_gratia_admin_webpage (self):
        core.skip_ok_unless_installed('gratia-service')
        host = socket.gethostname()
        admin_webpage = 'http://' + host + ':8880/gratia-administration/status.html?wantDetails=0'
        command = ('curl', admin_webpage)
        core.check_system(command, 'Unable to launch gratia admin webpage')
        
    #===============================================================================
    # This test counts the number of lines in the "show databases" command output
    #===============================================================================
    def test_02_show_databases(self):
        core.skip_ok_unless_installed('gratia-service')    
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        #Command to show the databases is:
        #echo "show databases;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" -B --unbuffered  --user=root --port=3306         
        command = "echo \"show databases;\" | mysql --defaults-extra-file=\"" + filename + "\" -B --unbuffered  --user=root --port=3306 | wc -l",
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to install Gratia Database !')
        print "show_databases stdout is: " + stdout
        result = re.search('5', stdout, re.IGNORECASE)
        self.assert_(result is not None)
        os.remove(filename)
        
    #===============================================================================
    # This test counts the number of lines in the gratia database tables output
    #===============================================================================
    def test_03_show_gratia_database_tables(self):
        core.skip_ok_unless_installed('gratia-service')    
        
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        #open the above file and write admin password information on the go
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        
        #Command to show the tabes in the gratia database is:
        #echo "use gratia;show tables;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" -B --unbuffered  --user=root --port=3306         
        command = "echo \"use gratia;show tables;\" | mysql --defaults-extra-file=\"" + filename + "\" -B --unbuffered  --user=root --port=3306 | wc -l",
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to install Gratia Database !')
        print "show_gratia_database_tables stdout is: " + stdout
        #Note that the actual output is 81 but the search below
        #is for 82 to account for the header row
        result = re.search('82', stdout, re.IGNORECASE)
        self.assert_(result is not None)
        os.remove(filename)
        
    #===============================================================================
    # This test customizes /etc/gratia/gridftp-transfer/ProbeConfig file
    #===============================================================================
    def test_04_modify_gridftptransfer_probeconfig(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        host = socket.gethostname()
        probeconfig = "/etc/gratia/gridftp-transfer/ProbeConfig"
        #Note that the blank spaces in some of the lines below have been
        #intentionally added to align with rest of the file
        collectorhost = "    CollectorHost=\"" + host + ":8880\""
        sslhost = "    SSLHost=\"" + host + ":8443\""
        sslregistrationhost = "    SSLRegistrationHost=\"" + host + ":8880\""
        self.patternreplace(probeconfig, "CollectorHost", collectorhost)
        self.patternreplace(probeconfig, "SSLHost", sslhost)
        self.patternreplace(probeconfig, "SSLRegistrationHost", sslregistrationhost)
        self.patternreplace(probeconfig, "SiteName", "    SiteName=\"OSG Test site\"")
        self.patternreplace(probeconfig, "EnableProbe", "    EnableProbe=\"1\"")
        
    #===============================================================================
    # This test copies gridftp.log and gridftp-auth.log files from SVN to /var/log
    #===============================================================================
    def test_05_copy_gridftp_logs(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        grid_ftp_log = os.path.join(get_python_lib(), 'files', 'gridftp.log')
        grid_ftp_auth_log = os.path.join(get_python_lib(), 'files', 'gridftp-auth.log')
        dst_dir = '/var/log'
        shutil.copy(grid_ftp_log, dst_dir)
        shutil.copy(grid_ftp_auth_log, dst_dir)
        print("test_05_copy_gridftp_logs - content of /var/log:\n" + str(os.listdir('/var/log')))
    
    #===============================================================================
    # This test executes the GridftpTransferProbeDriver
    #===============================================================================
    def test_06_execute_gridftptransfer_probedriver(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        command = ('/usr/share/gratia/gridftp-transfer/GridftpTransferProbeDriver',)
        core.check_system(command, 'Unable to execute GridftpTransferProbeDriver!')
        host = socket.gethostname()
        core.config['gratia.gridftp-temp-dir'] = "/var/lib/gratia/tmp/gratiafiles/subdir.gridftp-transfer_" + host + "_" + host + "_8880"
        outboxdir = core.config['gratia.gridftp-temp-dir'] + "/outbox/"
        print("test_06_execute_gridftptransfer_probedriver outboxdir is: " + outboxdir)
        #Need to check if the above outboxdir is empty
        self.assert_(not os.listdir(outboxdir), 'gridftp-transfer outbox NOT empty !')
        core.state['gratia.gridftp-transfer-running'] = True
        
    #===============================================================================
    # This test checks the database after 
    # the successful execution of GridftpTransferProbeDriver
    #===============================================================================
    def test_07_checkdatabase_gridftptransfer_probedriver(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        self.skip_bad_if(core.state['gratia.gridftp-transfer-running'] == False)   
       
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        #open the above file and write admin password information on the go
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        
        #Command to check the database is:
        #echo "use gratia; select sum(Njobs), sum(TransferSize) from MasterTransferSummary;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" --skip-column-names -B --unbuffered  --user=root --port=3306         
        #command = "echo \"use gratia; select sum(Njobs), sum(TransferSize) from MasterTransferSummary;\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        #_, stdout, _ = core.check_system(command, 'Unable to query Gratia Database MasterTransferSummary table !', shell=True)
        
        #The stdout (based on fixed gridftp-auth.log and gridftp.log) should look as follows
        #mysql> select sum(Njobs), sum(TransferSize) from MasterTransferSummary;
        #+------------+-------------------+
        #| sum(Njobs) | sum(TransferSize) |
        #+------------+-------------------+
        #|       1167 |      220545414576 | 
        #+------------+-------------------+
        #1 row in set (0.00 sec)
        #The assertions below try to search for the numbers presented above
        
        #Per Tanya, need to sleep for a minute or so to allow gratia to "digest" probe data
        #Need a more deterministic way to make this work other than waiting for a random time...
        time.sleep(60)
        
        command = "echo \"use gratia; select sum(Njobs) from MasterTransferSummary;\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        _, stdout, _ = core.check_system(command, 'Unable to query Gratia Database MasterTransferSummary table !', shell=True)
        #status, stdout, _ = core.system(command, shell=True)
        #self.assertEqual(status, 0, 'Unable to query Gratia Database MasterTransferSummary table !')
        print "select sum(Njobs) stdout is: "
        print stdout
        result1 = re.search('1167', stdout, re.IGNORECASE)
        self.assert_(result1 is not None)
        
        
        command = "echo \"use gratia; select sum(TransferSize) from MasterTransferSummary;\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        _, stdout, _ = core.check_system(command, 'Unable to query Gratia Database MasterTransferSummary table !', shell=True)
        #status, stdout, _ = core.system(command, shell=True)
        #self.assertEqual(status, 0, 'Unable to query Gratia Database MasterTransferSummary table !')
        result2 = re.search('220545414576', stdout, re.IGNORECASE)
        print "select sum(TransferSize) stdout is: "
        print stdout
        self.assert_(result2 is not None)
        os.remove(filename)