import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest
import os
import re
from distutils.sysconfig import get_python_lib
import shutil
import socket
import time
import fnmatch


class TestGratia(osgunittest.OSGTestCase):
    
    #This method is taken from test_28 - we can consider moving it to core.py module
    #===========================================================================
    # This helper method loops through the passed in infile line by line. 
    # If it finds the passed in pattern in a line, it EITHER replaces the whole line 
    # with the passed in full_line OR inserts it after the line, depending on the
    # desired input
    #===========================================================================
    def patternreplace(self, infile_name, pattern, full_line, insert_after="no"):
        infile = open(infile_name, "r")
        outfile_name = infile_name + ".tmp"
        outfile = file(outfile_name, 'w')
        
        #If the pattern is found in a non-comment line, replace the line with the passed in "full_line"
        for line in infile:
            if pattern in line and not line.startswith('#'):
                if(insert_after=="no"): #Default case, just replace the line
                    line = full_line + "\n"
                else: #Insert the passed in line AFTER the line in which the pattern was found
                    line = line + full_line + "\n"
            outfile.writelines(line)
        outfile.close()
        infile.close()
        
        shutil.move(outfile_name, infile_name)


    #===========================================================================
    # This helper method copies user-vo-map in /var/lib/osg, if not already present
    #===========================================================================
    def copy_user_vo_map_file(self):
        user_vo_map_dir = '/var/lib/osg/'
        user_vo_map_file = os.path.join(get_python_lib(), 'files', 'user-vo-map')
        if not (os.path.exists(user_vo_map_dir)):
            os.makedirs(user_vo_map_dir)
            shutil.copy(user_vo_map_file, user_vo_map_dir)
            print ("/var/lib/osg/ did not exist before - created it and added the file")
        elif not (os.path.exists(os.path.join(user_vo_map_dir,'user-vo-map'))): #directory exists, copy file, if the file is not already present
            shutil.copy(user_vo_map_file, user_vo_map_dir)
            print ("/var/lib/osg/ existed but the file did NOT exist before - added the file")
        else: #both directory and file are present and so, do nothing...
            print ("/var/lib/osg/ AND the file existed before - No further action needed")
            pass
        print("content of /var/lib/osg/:\n" + str(os.listdir('/var/lib/osg/')))

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
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer')
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
    # This test copies the necessary files to to /var/log and /var/lib/osg/ directories
    #===============================================================================
    def test_05_copy_gridftp_logs(self):
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer')
        #=======================================================================
        # grid_ftp_log = os.path.join(get_python_lib(), 'files', 'gridftp.log')
        # grid_ftp_auth_log = os.path.join(get_python_lib(), 'files', 'gridftp-auth.log')
        # dst_dir = '/var/log'
        # shutil.copy(grid_ftp_log, dst_dir)
        # shutil.copy(grid_ftp_auth_log, dst_dir)
        #=======================================================================
        print("test_05_copy_gridftp_logs - content of /var/log:\n" + str(os.listdir('/var/log')))
        self.copy_user_vo_map_file()

    
    #===============================================================================
    # This test executes the GridftpTransferProbeDriver
    #===============================================================================
    def test_06_execute_gridftptransfer_probedriver(self):
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer')
        command = ('/usr/share/gratia/gridftp-transfer/GridftpTransferProbeDriver',)
        core.check_system(command, 'Unable to execute GridftpTransferProbeDriver!')
        if(core.state['gratia.database-installed'] == True):
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
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer, gratia-service')
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
        #_, stdout, _ = core.check_system(command, 'Unable to query Gratia Database MasterTransferSummary table !', shell=True)
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database MasterTransferSummary table !')
        print "select sum(Njobs) stdout is: "
        print stdout
        result1 = re.search('4', stdout, re.IGNORECASE)
        self.assert_(result1 is not None)
        
        
        command = "echo \"use gratia; select sum(TransferSize) from MasterTransferSummary;\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        #_, stdout, _ = core.check_system(command, 'Unable to query Gratia Database MasterTransferSummary table !', shell=True)
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database MasterTransferSummary table !')
        result2 = re.search('232', stdout, re.IGNORECASE)
        print "select sum(TransferSize) stdout is: "
        print stdout
        self.assert_(result2 is not None)
        os.remove(filename)
        
    #===============================================================================
    # This test customizes /etc/gratia/glexec/ProbeConfig file
    #===============================================================================
    def test_08_modify_glexec_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-glexec')
        host = socket.gethostname()
        probeconfig = "/etc/gratia/glexec/ProbeConfig"
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
        self.patternreplace(probeconfig, "gLExecMonitorLog", "    gLExecMonitorLog=\"/var/log/glexec.log\"")
        
    #===============================================================================
    # This test copies glexec.log file from SVN to /var/log
    #===============================================================================
    def test_09_copy_glexec_logs(self):
        core.skip_ok_unless_installed('gratia-probe-glexec')
        glexec_log = os.path.join(get_python_lib(), 'files', 'glexec.log')
        dst_dir = '/var/log'
        shutil.copy(glexec_log, dst_dir)
        print("test_09_copy_glexec_logs - content of /var/log:\n" + str(os.listdir('/var/log')))
        self.copy_user_vo_map_file()

    #===============================================================================
    # This test executes glexec_meter
    #===============================================================================
    def test_10_execute_glexec_meter(self):
        core.skip_ok_unless_installed('gratia-probe-glexec')
        command = ('/usr/share/gratia/glexec/glexec_meter',)
        core.check_system(command, 'Unable to execute glexec_meter!')
        host = socket.gethostname()
        core.config['gratia.glexec-temp-dir'] = "/var/lib/gratia/tmp/gratiafiles/subdir.glexec_" + host + "_" + host + "_8880"
        outboxdir = core.config['gratia.glexec-temp-dir'] + "/outbox/"
        print("test_10_execute_glexec_meter outboxdir is: " + outboxdir)
        #Need to check if the above outboxdir is empty
        self.assert_(not os.listdir(outboxdir), 'glexec_meter outbox NOT empty !')
        core.state['gratia.glexec_meter-running'] = True
        
    #===============================================================================
    # This test checks the database after 
    # the successful execution of glexec_meter
    #===============================================================================
    def test_11_checkdatabase_glexec_meter(self):
        core.skip_ok_unless_installed('gratia-probe-glexec')
        self.skip_bad_if(core.state['gratia.glexec_meter-running'] == False)   
       
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        #open the above file and write admin password information on the go
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        
        #Per Tanya, need to sleep for a minute or so to allow gratia to "digest" probe data
        #Need a more deterministic way to make this work other than waiting for a random time...
        time.sleep(60)
        
        command = "echo \"use gratia; select Njobs from MasterSummaryData where ProbeName like 'glexec%';\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database Njobs from MasterSummaryData table !')
        print "select Njobs stdout is: "
        print stdout
        result1 = re.search('4', stdout, re.IGNORECASE)
        self.assert_(result1 is not None)
        
        
        command = "echo \"use gratia; select WallDuration from MasterSummaryData where ProbeName like 'glexec%';\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database WallDuration from MasterSummaryData table !')
        print "select WallDuration stdout is: "
        print stdout
        result2 = re.search('302', stdout, re.IGNORECASE)
        self.assert_(result2 is not None)
        os.remove(filename)
        
    #===============================================================================
    # This test customizes /etc/gratia/dCache-storage/ProbeConfig file
    #===============================================================================
    def test_12_modify_dcache_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage')
        host = socket.gethostname()
        probeconfig = "/etc/gratia/dCache-storage/ProbeConfig"
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
        self.patternreplace(probeconfig, "InfoProviderUrl", "    InfoProviderUrl=\"http://fndca3a.fnal.gov:2288/info\"")


    #===============================================================================
    # This test copies logs for dcache probe
    #===============================================================================
    def test_13_copy_dcache_logs(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage')
        self.copy_user_vo_map_file()

    #===============================================================================
    # This test executes dCache-storage
    #===============================================================================
    def test_14_execute_dcache_storage(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage')
        command = ('/usr/share/gratia/dCache-storage/dCache-storage_meter.cron.sh',)
        core.check_system(command, 'Unable to execute dCache-storage!')
        # clean up the following directory:
        # /var/lib/gratia/tmp/gratiafiles/subdir.dCache-storage_fermicloud339.fnal.gov_fermicloud339.fnal.gov_8880
        host = socket.gethostname()
        core.config['gratia.dcache-temp-dir'] = "/var/lib/gratia/tmp/gratiafiles/subdir.dCache-storage_" + host + "_" + host + "_8880"
        outboxdir = core.config['gratia.dcache-temp-dir'] + "/outbox/"
        print("test_14_execute_dcache_storage outboxdir is: " + outboxdir)
        #Need to check if the above outboxdir is empty
        self.assert_(not os.listdir(outboxdir), 'dCache-storage outbox NOT empty !')
        core.state['gratia.dcache-storage-running'] = True
    
    #===============================================================================
    # This test checks the database after 
    # the successful execution of dCache-storage
    #===============================================================================
    def test_15_checkdatabase_dcache_storage(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage')
        self.skip_bad_if(core.state['gratia.dcache-storage-running'] == False)   
       
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        #open the above file and write admin password information on the go
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        
        #Per Tanya, need to sleep for a minute or so to allow gratia to "digest" probe data
        #Need a more deterministic way to make this work other than waiting for a random time...
        time.sleep(60)
        
        command = "echo \"use gratia; select TotalSpace from StorageElementRecord where ProbeName like 'dCache-storage%';\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        status, TotalSpace, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database TotalSpace from StorageElementRecord table !')
        print "TotalSpace is: "
        print TotalSpace

        command = "echo \"use gratia; select FreeSpace from StorageElementRecord where ProbeName like 'dCache-storage%';\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        status, FreeSpace, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database FreeSpace from StorageElementRecord table !')
        print "FreeSpace is: "
        print FreeSpace
        
        command = "echo \"use gratia; select UsedSpace from StorageElementRecord where ProbeName like 'dCache-storage%';\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        status, UsedSpace, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database UsedSpace from StorageElementRecord table !')
        print "UsedSpace is: "
        print UsedSpace
        
        #Need to assert only after converting string to integers...
        self.assert_(int(TotalSpace) == (int(FreeSpace) + int(UsedSpace)))
        os.remove(filename)
        
    #===============================================================================
    # This test customizes /etc/gratia/condor/ProbeConfig file
    #===============================================================================
    def test_16_modify_condor_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-condor')
        host = socket.gethostname()
        probeconfig = "/etc/gratia/condor/ProbeConfig"
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
    # This test copies condor probe related files from SVN to /var/log
    #===============================================================================
    def test_17_copy_condor_logs(self):
        core.skip_ok_unless_installed('gratia-probe-condor')
#===============================================================================
#         certinfo_12110 = os.path.join(get_python_lib(), 'files', 'gratia_certinfo_condor_12110')
#         certinfo_12111 = os.path.join(get_python_lib(), 'files', 'gratia_certinfo_condor_12111')
#         certinfo_12112 = os.path.join(get_python_lib(), 'files', 'gratia_certinfo_condor_12112')
#         certinfo_12113 = os.path.join(get_python_lib(), 'files', 'gratia_certinfo_condor_12113')
#         certinfo_12114 = os.path.join(get_python_lib(), 'files', 'gratia_certinfo_condor_12114')
#         certinfo_12115 = os.path.join(get_python_lib(), 'files', 'gratia_certinfo_condor_12115')
#         certinfo_12116 = os.path.join(get_python_lib(), 'files', 'gratia_certinfo_condor_12116')
#         history_12110 = os.path.join(get_python_lib(), 'files', 'history.12110.0')
#         history_12111 = os.path.join(get_python_lib(), 'files', 'history.12111.0')
#         history_12112 = os.path.join(get_python_lib(), 'files', 'history.12112.0')
#         history_12113 = os.path.join(get_python_lib(), 'files', 'history.12113.0')
#         history_12114 = os.path.join(get_python_lib(), 'files', 'history.12114.0')
#         history_12115 = os.path.join(get_python_lib(), 'files', 'history.12115.0')
#         history_12116 = os.path.join(get_python_lib(), 'files', 'history.12116.0')
# 
#         dst_dir = '/var/lib/gratia/data'
#         shutil.copy(certinfo_12110, dst_dir)
#         shutil.copy(certinfo_12111, dst_dir)
#         shutil.copy(certinfo_12112, dst_dir)
#         shutil.copy(certinfo_12113, dst_dir)
#         shutil.copy(certinfo_12114, dst_dir)
#         shutil.copy(certinfo_12115, dst_dir)
#         shutil.copy(certinfo_12116, dst_dir)
#         shutil.copy(history_12110, dst_dir)
#         shutil.copy(history_12111, dst_dir)
#         shutil.copy(history_12112, dst_dir)
#         shutil.copy(history_12113, dst_dir)
#         shutil.copy(history_12114, dst_dir)
#         shutil.copy(history_12115, dst_dir)
#         shutil.copy(history_12116, dst_dir)
#===============================================================================
        
        print("test_17_copy_condor_logs - content of /var/lib/gratia/data:\n" + str(os.listdir('/var/lib/gratia/data')))
        self.copy_user_vo_map_file()
        
    #===============================================================================
    # This test starts condor service, if not already running
    #===============================================================================
    def test_18_execute_condor(self):
        core.skip_ok_unless_installed('gratia-probe-condor')  
        
        self.skip_ok_if(core.state['condor.running-service'] == True, 'Already started condor service')
        
        #If the service was not already started, start it now...
        command = ('service', 'condor', 'start')
        stdout, _, fail = core.check_system(command, 'Start Condor')
        self.assert_(stdout.find('error') == -1, fail)
        #self.assert_(os.path.exists(core.config['condor.lockfile']),
        #            'Condor run lock file missing')
        core.state['condor.started-service'] = True
        core.state['condor.running-service'] = True
        
    #===============================================================================
    # This test executes condor_meter
    #===============================================================================
    def test_19_execute_condor_meter(self):
        core.skip_ok_unless_installed('gratia-probe-condor')  
        self.skip_ok_if(core.state['condor.running-service'] == False, 'Need to have condor service running !')    
        command = ('/usr/share/gratia/condor/condor_meter',)
        core.check_system(command, 'Unable to execute condor_meter !')
        if(core.state['gratia.database-installed'] == True):
            host = socket.gethostname()
            core.config['gratia.condor-temp-dir'] = "/var/lib/gratia/tmp/gratiafiles/subdir.condor_" + host + "_" + host + "_8880"
            outboxdir = core.config['gratia.condor-temp-dir'] + "/outbox/"
            print("test_18_execute_condor_meter outboxdir is: " + outboxdir)
            #Need to check if the above outboxdir is empty
            self.assert_(not os.listdir(outboxdir), 'condor outbox NOT empty !')
        core.state['gratia.condor-meter-running'] = True


    #===============================================================================
    # This test checks database after condor_meter is run
    #===============================================================================
    def test_20_checkdatabase_condor_meter(self):
        core.skip_ok_unless_installed('gratia-probe-condor, gratia-service')  
        self.skip_bad_if(core.state['gratia.condor-meter-running'] == False, 'Need to have condor-meter running !')           
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        #open the above file and write admin password information on the go
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        
        #Per Tanya, need to sleep for a minute or so to allow gratia to "digest" probe data
        #Need a more deterministic way to make this work other than waiting for a random time...
        time.sleep(60)
        
        command = "echo \"use gratia; select sum(Njobs) from MasterSummaryData where ProbeName like 'condor%';\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database Njobs from MasterSummaryData table !')
        print "select sum(Njobs) stdout is: "
        print stdout
        result1 = re.search('7', stdout, re.IGNORECASE)
        self.assert_(result1 is not None)
        
        
        command = "echo \"use gratia; select sum(WallDuration) from MasterSummaryData where ProbeName like 'condor%';\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database WallDuration from MasterSummaryData table !')
        print "select sum(WallDuration) stdout is: "
        print stdout
        result2 = re.search('69', stdout, re.IGNORECASE)
        self.assert_(result2 is not None)
        os.remove(filename)
        
    #===============================================================================
    # This test customizes /etc/gratia/psacct/ProbeConfig file
    #===============================================================================
    def test_21_modify_psacct_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-psacct')
        host = socket.gethostname()
        probeconfig = "/etc/gratia/psacct/ProbeConfig"
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
        self.patternreplace(probeconfig, "Grid=", "    Grid=\"Local\"")
        self.patternreplace(probeconfig, "QuarantineUnknownVORecords=", "    QuarantineUnknownVORecords=\"0\"")

        
    #===========================================================================
    # This test starts the psacct service
    #===========================================================================
    def test_22_start_psacct_service(self):
        core.skip_ok_unless_installed('gratia-probe-psacct')
        command = ('service', 'psacct', 'start')
        stdout, _, fail = core.check_system(command, 'Start psacct')
        self.assert_(stdout.find('error') == -1, fail)
        
    #===============================================================================
    # This test executes psacct
    #===============================================================================
    def test_23_execute_psacct(self):
        core.skip_ok_unless_installed('gratia-probe-psacct')  
        command = ('/usr/share/gratia/psacct/psacct_probe.cron.sh',)
        core.check_system(command, 'Unable to execute psacct!')
        host = socket.gethostname()
        core.config['gratia.psacct-temp-dir'] = "/var/lib/gratia/tmp/gratiafiles/subdir.psacct_" + host + "_" + host + "_8880"
        outboxdir = core.config['gratia.psacct-temp-dir'] + "/outbox/"
        print("test_23_execute_psacct outboxdir is: " + outboxdir)
        #Need to check if the above outboxdir is empty
        self.assert_(not os.listdir(outboxdir), 'psacct outbox NOT empty !')
        core.state['gratia.psacct-running'] = True


    #===============================================================================
    # This test checks database after psacct is run
    #===============================================================================
    def test_24_checkdatabase_psacct(self):
        core.skip_ok_unless_installed('gratia-probe-psacct')  
        self.skip_bad_if(core.state['gratia.psacct-running'] == False, 'Need to have psacct running !')           
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        #open the above file and write admin password information on the go
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        
        #Per Tanya, need to sleep for a minute or so to allow gratia to "digest" probe data
        #Need a more deterministic way to make this work other than waiting for a random time...
        time.sleep(60)
        
        command = "echo \"use gratia; select * from MasterSummaryData where ProbeName like 'psac%' and ResourceType='RawCPU';\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306 | wc -l",
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database table !')
        print "ProbeName like 'psac%' and ResourceType=\"RawCPU\" stdout is: "
        print stdout
  
        self.assert_(int(stdout) >= 1, 'Query should return at least ONE record !') #Assert that the query returned at least ONE record
        os.remove(filename)

    #===============================================================================
    # This test customizes /etc/gratia/bdii-status/ProbeConfig file
    #===============================================================================
    def test_25_modify_bdii_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-bdii-status')
        host = socket.gethostname()
        probeconfig = "/etc/gratia/bdii-status/ProbeConfig"
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
    # This test executes bdii-status
    #===============================================================================
    def test_26_execute_bdii_status(self):
        core.skip_ok_unless_installed('gratia-probe-bdii-status')  
        command = ('/usr/share/gratia/bdii-status/bdii_cese_record',)
        core.check_system(command, 'Unable to execute bdii-status!')
        host = socket.gethostname()
        core.config['gratia.bdii-temp-dir'] = "/var/lib/gratia/tmp/gratiafiles/subdir.bdii_" + "*" + host + "_" + host + "_8880"
        for file in os.listdir('/var/lib/gratia/tmp/gratiafiles/'):
            if fnmatch.fnmatch(file, '*bdii*'):
                outboxdir = "/var/lib/gratia/tmp/gratiafiles/" + file + "/outbox/"
                print("test_26_execute_bdii_status outboxdir is: " + outboxdir)
                #Apparently, there's a bug in the probe, due to which outbox is NOT getting cleaned up
                #Tanya is investigating it and hence, commenting the outbox check for now
                #Need to check if the above outboxdir is empty
                #time.sleep(60)
                #self.assert_(not os.listdir(outboxdir), 'bdii outbox NOT empty !')
        core.state['gratia.bdii-status-running'] = True
        
        
    #===============================================================================
    # This test checks database after bdii-status is run
    #===============================================================================
    def test_27_checkdatabase_bdii_status(self):
        core.skip_ok_unless_installed('gratia-probe-bdii-status')  
        self.skip_bad_if(core.state['gratia.bdii-status-running'] == False, 'Need to have gratia-probe-bdii-status running !')           
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        #open the above file and write admin password information on the go
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        
        #Per Tanya, need to sleep for a minute or so to allow gratia to "digest" probe data
        #Need a more deterministic way to make this work other than waiting for a random time...
        time.sleep(60)
        
        command = "echo \"use gratia; select count(*) from ComputeElement where SiteName='USCMS-FNAL-WC1' and LRMSType='condor';\" | mysql --defaults-extra-file=\"" + filename + "\" --skip-column-names -B --unbuffered  --user=root --port=3306",
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database table !')
        print "count(*) from ComputeElement where SiteName='USCMS-FNAL-WC1' and LRMSType='condor' stdout is: "
        print stdout
  
        self.assert_(int(stdout) >= 1, 'Query should return at least ONE record') #Assert that the query returned at least ONE record
        os.remove(filename)
        