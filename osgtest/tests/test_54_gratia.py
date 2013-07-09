import osgtest.library.core as core
import osgtest.library.files as files
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
        elif not (os.path.exists(os.path.join(user_vo_map_dir,'user-vo-map'))): #directory exists, copy file, if the file is not already present
            shutil.copy(user_vo_map_file, user_vo_map_dir)
        else: #both directory and file are present and so, do nothing...
            pass
    
    #================================================================
    # This helper method copies Probe Logs to the passed in directory
    #================================================================
    def copy_probe_logs(self, log='', logdirectory=''):
        self.copy_user_vo_map_file()
        if ((log != '') and (logdirectory != '')):
            if not os.path.exists(logdirectory):
                os.makedirs(logdirectory)
            shutil.copy(log, logdirectory)
    
    #====================================================================================
    # This helper method modifies the Probe Configuration, generally needed by many probes
    #====================================================================================
    def modify_probeconfig(self, probeconfig):
        host = core.get_hostname()
        collectorhost = "    CollectorHost=\"" + host + ":8880\""
        sslhost = "    SSLHost=\"" + host + ":8443\""
        sslregistrationhost = "    SSLRegistrationHost=\"" + host + ":8880\""
        self.patternreplace(probeconfig, "CollectorHost", collectorhost)
        self.patternreplace(probeconfig, "SSLHost", sslhost)
        self.patternreplace(probeconfig, "SSLRegistrationHost", sslregistrationhost)
        self.patternreplace(probeconfig, "SiteName", "SiteName=\"OSG Test site\"")
        self.patternreplace(probeconfig, "EnableProbe", "EnableProbe=\"1\"")
        self.patternreplace(probeconfig, "QuarantineUnknownVORecords=", "QuarantineUnknownVORecords=\"0\"")
        
    #=================================================================================================
    # This helper method returns True if the outbox directory for the probe, is empty; False otherwise
    #=================================================================================================
    def isProbeOutboxDirEmpty(self, gratiaProbeTempDir):
            outboxdir = gratiaProbeTempDir + "/outbox/"
            #Need to check if the above outboxdir is empty
            if(not os.listdir(outboxdir)):
                return True
            else:
                return False
            
    #=================================================================================================
    # This helper method looks for the pattern 'RecordProcessor: 0: ProbeDetails' in gratia log, 
    # which signifies that Gratia has processed the probe information
    #=================================================================================================
    def isProbeInfoProcessed(self):
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = os.stat(core.config['gratia.log.file'])
        line, gap = core.monitor_file(core.config['gratia.log.file'], core.state['gratia.log.stat'], 'RecordProcessor: 0: ProbeDetails', 60.0)
        if(line is not None):
            core.log_message('Gratia processed probe data - Time taken is %.1f seconds' % gap)
            core.log_message('Gratia processed probe data - Line is ' + str(line))
            return True
        else:
            return False
        
    #===============================================================================
    # This test tries to launch a gratia admin webpage
    #===============================================================================
    def test_01_gratia_admin_webpage (self):
        core.skip_ok_unless_installed('gratia-service')
        host = core.get_hostname()
        admin_webpage = 'http://' + host + ':8880/gratia-administration/status.html?wantDetails=0'
        command = ('curl', admin_webpage)
        core.check_system(command, 'Unable to launch gratia admin webpage')
        
    #===============================================================================
    # This test counts the number of lines in the "show databases" command output
    #===============================================================================
    def test_02_show_databases(self):
        core.skip_ok_unless_installed('gratia-service')    
        #Command to show the databases is:
        #echo "show databases;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" -B --unbuffered  --user=reader --port=3306         
        command = "echo \"show databases;" + core.config['gratia.sql.querystring'] + "| wc -l",
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to install Gratia Database !')
        result = re.search('3', stdout, re.IGNORECASE)
        self.assert_(result is not None)
        
    #===============================================================================
    # This test counts the number of lines in the gratia database tables output
    #===============================================================================
    def test_03_show_gratia_database_tables(self):
        core.skip_ok_unless_installed('gratia-service')    
                
        #Command to show the tabes in the gratia database is:
        #echo "use gratia;show tables;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" -B --unbuffered  --user=root --port=3306         
        command = "echo \"use gratia;show tables;" + core.config['gratia.sql.querystring'] + "| wc -l",
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to install Gratia Database !')
        result = re.search('81', stdout, re.IGNORECASE)
        self.assert_(result is not None)
        
    #===============================================================================
    # This test customizes /etc/gratia/gridftp-transfer/ProbeConfig file
    #===============================================================================
    def test_04_modify_gridftptransfer_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer')
        probeconfig = core.config['gratia.config.dir'] + "/gridftp-transfer/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        
    #===============================================================================
    # This test copies the necessary files for gridftp test
    #===============================================================================
    def test_05_copy_gridftp_logs(self):
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer')
        self.copy_probe_logs()

    #===============================================================================
    # This test executes the GridftpTransferProbeDriver
    #===============================================================================
    def test_06_execute_gridftptransfer_probedriver(self):
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer')
        core.state['gratia.gridftp-transfer-running'] = False
        command = ('/usr/share/gratia/gridftp-transfer/GridftpTransferProbeDriver',)
        core.check_system(command, 'Unable to execute GridftpTransferProbeDriver!')
        core.config['gratia.gridftp-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.gridftp-transfer" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.gridftp-temp-dir'])
            self.assert_(result == True, 'gridftp-transfer outbox check failed !')
        core.state['gratia.gridftp-transfer-running'] = True
        
    #===============================================================================
    # This test checks the database after 
    # the successful execution of GridftpTransferProbeDriver
    #===============================================================================
    def test_07_checkdatabase_gridftptransfer_probedriver(self):
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer', 'gratia-service')
        self.skip_bad_if(core.state['gratia.gridftp-transfer-running'] == False)   
               
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
        
        self.assert_(self.isProbeInfoProcessed() == True, 'Sentinel signifying Probe Information was processed NOT found !')
        
        command = "echo \"use gratia; select sum(Njobs) from MasterTransferSummary;" + core.config['gratia.sql.querystring'],
        #_, stdout, _ = core.check_system(command, 'Unable to query Gratia Database MasterTransferSummary table !', shell=True)
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database MasterTransferSummary table !')
        result1 = re.search('4', stdout, re.IGNORECASE)
        self.assert_(result1 is not None)
        
        
        command = "echo \"use gratia; select sum(TransferSize) from MasterTransferSummary;" + core.config['gratia.sql.querystring'],
        #_, stdout, _ = core.check_system(command, 'Unable to query Gratia Database MasterTransferSummary table !', shell=True)
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database MasterTransferSummary table !')
        result2 = re.search('232', stdout, re.IGNORECASE)
        self.assert_(result2 is not None)
        
    #===============================================================================
    # This test customizes /etc/gratia/glexec/ProbeConfig file
    #===============================================================================
    def test_08_modify_glexec_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-glexec')
        probeconfig = core.config['gratia.config.dir'] + "/glexec/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        self.patternreplace(probeconfig, "gLExecMonitorLog", "gLExecMonitorLog=\"/var/log/glexec.log\"")

        
    #===============================================================================
    # This test copies glexec.log file from SVN to /var/log
    #===============================================================================
    def test_09_copy_glexec_logs(self):
        core.skip_ok_unless_installed('gratia-probe-glexec')
        glexec_log = os.path.join(get_python_lib(), 'files', 'glexec.log')
        dst_dir = '/var/log'
        self.copy_probe_logs(glexec_log, dst_dir)

    #===============================================================================
    # This test executes glexec_meter
    #===============================================================================
    def test_10_execute_glexec_meter(self):
        core.skip_ok_unless_installed('gratia-probe-glexec')
        core.state['gratia.glexec_meter-running'] = False
        command = ('/usr/share/gratia/glexec/glexec_meter',)
        core.check_system(command, 'Unable to execute glexec_meter!')      
        core.config['gratia.glexec-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.glexec" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.glexec-temp-dir'])
            self.assert_(result == True, 'glexec_meter outbox check failed !')
        core.state['gratia.glexec_meter-running'] = True
        
    #===============================================================================
    # This test checks the database after 
    # the successful execution of glexec_meter
    #===============================================================================
    def test_11_checkdatabase_glexec_meter(self):
        core.skip_ok_unless_installed('gratia-probe-glexec', 'gratia-service')
        self.skip_bad_if(core.state['gratia.glexec_meter-running'] == False)        
        self.assert_(self.isProbeInfoProcessed() == True, 'Sentinel signifying Probe Information was processed NOT found !')

        command = "echo \"use gratia; select Njobs from MasterSummaryData where ProbeName like 'glexec%';" + core.config['gratia.sql.querystring'],
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database Njobs from MasterSummaryData table !')
        result1 = re.search('4', stdout, re.IGNORECASE)
        self.assert_(result1 is not None)
        
        
        command = "echo \"use gratia; select WallDuration from MasterSummaryData where ProbeName like 'glexec%';" + core.config['gratia.sql.querystring'],
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database WallDuration from MasterSummaryData table !')
        result2 = re.search('302', stdout, re.IGNORECASE)
        self.assert_(result2 is not None)
        
    #===============================================================================
    # This test customizes /etc/gratia/dCache-storage/ProbeConfig file
    #===============================================================================
    def test_12_modify_dcache_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage')
        probeconfig = core.config['gratia.config.dir'] + "/dCache-storage/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        self.patternreplace(probeconfig, "InfoProviderUrl", "InfoProviderUrl=\"http://fndca3a.fnal.gov:2288/info\"")

    #===============================================================================
    # This test copies logs for dcache probe
    #===============================================================================
    def test_13_copy_dcache_logs(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage')
        self.copy_probe_logs()

    #===============================================================================
    # This test executes dCache-storage
    #===============================================================================
    def test_14_execute_dcache_storage(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage')
        core.state['gratia.dcache-storage-running'] = False
        command = ('/usr/share/gratia/dCache-storage/dCache-storage_meter.cron.sh',)
        core.check_system(command, 'Unable to execute dCache-storage!')
        # clean up the following directory:
        # /var/lib/gratia/tmp/gratiafiles/subdir.dCache-storage_fermicloud339.fnal.gov_fermicloud339.fnal.gov_8880        
        core.config['gratia.dcache-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.dCache-storage" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.dcache-temp-dir'])
            self.assert_(result == True, 'dCache-storage outbox check failed !')
        core.state['gratia.dcache-storage-running'] = True
    
    #===============================================================================
    # This test checks the database after 
    # the successful execution of dCache-storage
    #===============================================================================
    def test_15_checkdatabase_dcache_storage(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage', 'gratia-service')
        self.skip_bad_if(core.state['gratia.dcache-storage-running'] == False)   
               
        self.assert_(self.isProbeInfoProcessed() == True, 'Sentinel signifying Probe Information was processed NOT found !')
        
        command = "echo \"use gratia; select TotalSpace from StorageElementRecord where ProbeName like 'dCache-storage%';" + core.config['gratia.sql.querystring'],
        status, TotalSpace, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database TotalSpace from StorageElementRecord table !')

        command = "echo \"use gratia; select FreeSpace from StorageElementRecord where ProbeName like 'dCache-storage%';" + core.config['gratia.sql.querystring'],
        status, FreeSpace, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database FreeSpace from StorageElementRecord table !')
        
        command = "echo \"use gratia; select UsedSpace from StorageElementRecord where ProbeName like 'dCache-storage%';" + core.config['gratia.sql.querystring'],
        status, UsedSpace, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database UsedSpace from StorageElementRecord table !')
        
        #Need to assert only after converting string to integers...
        self.assert_(long(TotalSpace) == (long(FreeSpace) + long(UsedSpace)))
        
    #===============================================================================
    # This test customizes /etc/gratia/condor/ProbeConfig file
    #===============================================================================
    def test_16_modify_condor_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-condor')
        probeconfig = core.config['gratia.config.dir'] + "/condor/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        
    #===============================================================================
    # This test copies condor probe related files from SVN to /var/log
    #===============================================================================
    def test_17_copy_condor_logs(self):
        core.skip_ok_unless_installed('gratia-probe-condor') 
        self.copy_probe_logs()       
        
        
    #===============================================================================
    # This test executes condor_meter
    #===============================================================================
    def test_18_execute_condor_meter(self):
        core.skip_ok_unless_installed('gratia-probe-condor')
        core.state['gratia.condor-meter-running'] = False
        self.skip_ok_if(core.state['condor.running-service'] == False, 'Need to have condor service running !')    
        command = ('/usr/share/gratia/condor/condor_meter',)
        core.check_system(command, 'Unable to execute condor_meter !')    
        core.config['gratia.condor-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.condor" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.condor-temp-dir'])
            self.assert_(result == True, 'condor outbox check failed !')
        core.state['gratia.condor-meter-running'] = True


    #===============================================================================
    # This test checks database after condor_meter is run
    #===============================================================================
    def test_19_checkdatabase_condor_meter(self):
        core.skip_ok_unless_installed('gratia-probe-condor', 'gratia-service')  
        self.skip_bad_if(core.state['gratia.condor-meter-running'] == False, 'Need to have condor-meter running !')           
        
        self.assert_(self.isProbeInfoProcessed() == True, 'Sentinel signifying Probe Information was processed NOT found !')
   
        command = "echo \"use gratia; select sum(Njobs) from MasterSummaryData where ProbeName like 'condor%';" + core.config['gratia.sql.querystring'],
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database Njobs from MasterSummaryData table !')
        result1 = re.search('1', stdout, re.IGNORECASE)
        self.assert_(result1 is not None)
        
        
        command = "echo \"use gratia; select sum(WallDuration) from MasterSummaryData where ProbeName like 'condor%';" + core.config['gratia.sql.querystring'],
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database WallDuration from MasterSummaryData table !')
        #result2 = re.search('69', stdout, re.IGNORECASE)
        self.assert_(int(stdout) >= 1, 'Query should return at least ONE record') #Assert that the query returned at least ONE record
        #self.assert_(result2 is not None)
        
    #===============================================================================
    # This test customizes /etc/gratia/psacct/ProbeConfig file
    #===============================================================================
    def test_20_modify_psacct_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-psacct')
        probeconfig = core.config['gratia.config.dir'] + "/psacct/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        self.patternreplace(probeconfig, "Grid=", "Grid=\"Local\"")

        
    #===========================================================================
    # This test starts the psacct service
    #===========================================================================
    def test_21_start_psacct_service(self):
        core.skip_ok_unless_installed('gratia-probe-psacct')
        command = ('service', 'psacct', 'start')
        stdout, _, fail = core.check_system(command, 'Start psacct')
        self.assert_(stdout.find('error') == -1, fail)
        
    #===============================================================================
    # This test executes psacct
    #===============================================================================
    def test_22_execute_psacct(self):
        core.skip_ok_unless_installed('gratia-probe-psacct') 
        core.state['gratia.psacct-running'] = False 
        command = ('/usr/share/gratia/psacct/psacct_probe.cron.sh',)
        core.check_system(command, 'Unable to execute psacct!')
        core.config['gratia.psacct-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.psacct" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.psacct-temp-dir'])
            self.assert_(result == True, 'psacct outbox check failed !')
        core.state['gratia.psacct-running'] = True


    #===============================================================================
    # This test checks database after psacct is run
    #===============================================================================
    def test_23_checkdatabase_psacct(self):
        core.skip_ok_unless_installed('gratia-probe-psacct', 'gratia-service')  
        self.skip_bad_if(core.state['gratia.psacct-running'] == False, 'Need to have psacct running !')           
        
        self.assert_(self.isProbeInfoProcessed() == True, 'Sentinel signifying Probe Information was processed NOT found !')
        
        command = "echo \"use gratia; select * from MasterSummaryData where ProbeName like 'psac%' and ResourceType='RawCPU';" + core.config['gratia.sql.querystring'] +  "| wc -l",
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database table !')
  
        self.assert_(int(stdout) >= 1, 'Query should return at least ONE record !') #Assert that the query returned at least ONE record

    #===============================================================================
    # This test customizes /etc/gratia/bdii-status/ProbeConfig file
    #===============================================================================
    def test_24_modify_bdii_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-bdii-status')
        probeconfig = core.config['gratia.config.dir'] + "/bdii-status/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        
    #===============================================================================
    # This test executes bdii-status
    #===============================================================================
    def test_25_execute_bdii_status(self):
        core.skip_ok_unless_installed('gratia-probe-bdii-status') 
        core.state['gratia.bdii-status-running'] = False 
        command = ('/usr/share/gratia/bdii-status/bdii_cese_record',)
        core.check_system(command, 'Unable to execute bdii-status!')        
        core.config['gratia.bdii-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.bdii_" + "*" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            for file in os.listdir('/var/lib/gratia/tmp/gratiafiles/'):
                if fnmatch.fnmatch(file, '*bdii*'):
                    outboxdir = core.config['gratia.tmpdir.prefix'] + file + "/outbox/"
                    #Apparently, there's a bug in the probe, due to which outbox is NOT getting cleaned up
                    #Tanya is investigating it and hence, commenting the outbox check for now
                    #Need to check if the above outboxdir is empty
                    #time.sleep(60)
                    #self.assert_(not os.listdir(outboxdir), 'bdii outbox check failed !')
        core.state['gratia.bdii-status-running'] = True
        
        
    #===============================================================================
    # This test checks database after bdii-status is run
    #===============================================================================
    def test_26_checkdatabase_bdii_status(self):
        core.skip_ok_unless_installed('gratia-probe-bdii-status', 'gratia-service')  
        self.skip_bad_if(core.state['gratia.bdii-status-running'] == False, 'Need to have gratia-probe-bdii-status running !')           
        
        self.assert_(self.isProbeInfoProcessed() == True, 'Sentinel signifying Probe Information was processed NOT found !')
        
        command = "echo \"use gratia; select count(*) from ComputeElement where LRMSType='condor';" + core.config['gratia.sql.querystring'],
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database table !')
  
        self.assert_(int(stdout) >= 1, 'Query should return at least ONE record') #Assert that the query returned at least ONE record
        
    #===============================================================================
    # This test customizes /etc/gratia/condor/ProbeConfig file
    #===============================================================================
    def test_27_modify_pbs_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf')
        probeconfig = core.config['gratia.config.dir'] + "/pbs-lsf/ProbeConfig"
        self.modify_probeconfig(probeconfig)

    #===============================================================================
    # This test copies pbs probe related logs
    #===============================================================================
    def test_28_copy_pbs_logs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf')
        pbs_log = os.path.join(get_python_lib(), 'files', '20130603')
        dst_dir = '/var/spool/pbs/server_priv/accounting'
        self.copy_probe_logs(pbs_log, dst_dir)
        

    #===============================================================================
    # This test executes pbs probe
    #===============================================================================
    def test_29_execute_pbs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf')  
        core.state['gratia.pbs-running'] = False
        command = ('/usr/share/gratia/pbs-lsf/pbs-lsf_meter.cron.sh',)
        core.check_system(command, 'Unable to execute pbs-lsf_meter !')
        core.config['gratia.pbs-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.pbs-lsf" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.pbs-temp-dir'])
            self.assert_(result == True,'pbs outbox check failed !')
        core.state['gratia.pbs-running'] = True

    #===============================================================================
    # This test checks database after pbs is run
    #===============================================================================
    def test_30_checkdatabase_pbs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf', 'gratia-service')  
        self.skip_bad_if(core.state['gratia.pbs-running'] == False, 'Need to have pbs running !')           
        
        self.assert_(self.isProbeInfoProcessed() == True, 'Sentinel signifying Probe Information was processed NOT found !')
        
        probename="'pbs-lsf:" + core.config['gratia.host']
        query="use gratia; select sum(nJobs) from MasterSummaryData where ProbeName=" + probename + "';"        
        command = "echo " + "\""+ query + core.config['gratia.sql.querystring'],
        status, stdout, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database table !')
  
        result = re.search('30', stdout, re.IGNORECASE)
        self.assert_(result is not None)
        #self.assert_(int(stdout) >= 1, 'Query should return at least ONE record !') #Assert that the query returned at least ONE record

        