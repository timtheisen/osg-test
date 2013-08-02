import os
import re
from distutils.sysconfig import get_python_lib
import shutil
import socket
import time
import fnmatch
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestGratia(osgunittest.OSGTestCase):
    
    def patternreplace(self, infile_name, pattern, full_line, insert_after="no"):
        """This method is taken from test_28 - we can consider moving it to core.py module
     This helper method loops through the passed in infile line by line. 
     If it finds the passed in pattern in a line, it EITHER replaces the whole line 
     with the passed in full_line OR inserts it after the line, depending on the
     desired input"""

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


    def copy_user_vo_map_file(self):
        """This helper method copies user-vo-map in /var/lib/osg, if not already present"""

        user_vo_map_dir = '/var/lib/osg/'
        user_vo_map_file = '/usr/share/osg-test/user-vo-map'
        if not (os.path.exists(user_vo_map_dir)):
            os.makedirs(user_vo_map_dir)
            try:
                shutil.copy(user_vo_map_file, user_vo_map_dir)
            except IOError, e:
                core.log_message("Unable to copy file. %s" % e)
                return False
        elif not (os.path.exists(os.path.join(user_vo_map_dir,'user-vo-map'))): #directory exists, copy file, if the file is not already present
            try:
                shutil.copy(user_vo_map_file, user_vo_map_dir)
            except IOError, e:
                core.log_message("Unable to copy file. %s" % e)
                return False
        else: #both directory and file are present and so, do nothing...
            core.log_message(str(os.listdir(user_vo_map_dir)))
            return True
        
        
    
    def copy_probe_logs(self, log='', logdirectory=''):
        """This helper method copies Probe Logs to the passed in directory"""

        if (self.copy_user_vo_map_file() == False):
            return False
        else:
            if ((log != '') and (logdirectory != '')):
                try:
                    if not os.path.exists(logdirectory):
                        os.makedirs(logdirectory)
                    shutil.copy(log, logdirectory)
                    core.log_message(str(os.listdir(logdirectory)))
                except IOError, e:
                    core.log_message("Unable to copy log. %s" % e)
                    return False
        #If we've reached this far, it's a success
        return True
    
    def modify_probeconfig(self, probeconfig):
        """This helper method modifies the Probe Configuration, generally needed by many probes"""

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
        
    def isProbeOutboxDirEmpty(self, gratiaProbeTempDir):
            """This helper method returns True if the outbox directory for the probe, is empty; False otherwise"""

            outboxdir = gratiaProbeTempDir + "/outbox/"
            #Need to check if the above outboxdir is empty
            try:
                core.log_message('isProbeOutboxDirEmpty method - outboxdir is: ' + str(outboxdir))
                if(not os.listdir(outboxdir)):
                    return True
                else:
                    return False
            except:
                raise
                return False            

    def isProbeInfoProcessed(self, ProbePattern):
        """This helper method parses gratia log for patterns signifying that Gratia has processed the probe information
    A. It loops through the lines with the pattern 'RecordProcessor: 0: ProbeDetails'
    B. Examines the output line to check if it contains the passed in Probe specific pattern, / AND the word saved
    Sample target lines from a gratia log is:
       2013-07-14 17:21:48,073 gratia.service(Thread-66) [FINE]: RecordProcessor: 0: ProbeDetails 9 / 9 
       (gridftp-transfer:fermicloud101.fnal.gov, recordId= Record 
       (Id: fermicloud101.fnal.gov:3274.0 CreateTime: 14 July 2013 at 22:21:37 GMT KeyInfo: null) ) saved.

        2013-07-14 17:22:18,161 gratia.service(Thread-66) [FINE]: RecordProcessor: 0: ProbeDetails 5 / 5
        (glexec:fermicloud101.fnal.gov, recordId= Record 
        (Id: fermicloud101.fnal.gov:3299.0 CreateTime: 14 July 2013 at 22:21:48 GMT KeyInfo: null) ) saved.
    
        2013-07-14 17:22:48,204 gratia.service(Thread-66) [FINE]: RecordProcessor: 0: ProbeDetails 3 / 3
        (dCache-storage:fermicloud101.fnal.gov, recordId= Record 
        (Id: fermicloud101.fnal.gov:3356.0 CreateTime: 14 July 2013 at 22:22:18 GMT KeyInfo: null) ) saved
    
        2013-07-14 17:23:18,294 gratia.service(Thread-66) [FINE]: RecordProcessor: 0: ProbeDetails 2 / 2
        (condor:fermicloud101.fnal.gov, recordId= Record 
        (Id: fermicloud101.fnal.gov:3390.0 CreateTime: 14 July 2013 at 22:22:48 GMT KeyInfo: null) ) saved.
    
        2013-07-14 17:23:48,346 gratia.service(Thread-66) [FINE]: RecordProcessor: 0: ProbeDetails 2 / 2
        (psacct:fermicloud101.fnal.gov, recordId= Record 
        (Id: fermicloud101.fnal.gov:3423.0 CreateTime: 14 July 2013 at 22:23:18 GMT KeyInfo: null) ) saved.
    
        2013-07-14 17:24:18,376 gratia.service(Thread-66) [FINE]: RecordProcessor: 0: ProbeDetails 
        (bdii-status:fermicloud101.fnal.gov, recordId= Record 
        (Id: fermicloud101.fnal.gov:3446.0 CreateTime: 14 July 2013 at 22:23:48 GMT KeyInfo: null) ) saved.
    
        2013-07-14 17:24:19,631 gratia.service(Thread-66) [FINE]: RecordProcessor: 0: ProbeDetails
        100 / 100 (bdii_compute:BNL-ATLAS-Condor:fermicloud101.fnal.gov, recordId= Record 
        (Id: fermicloud101.fnal.gov:3446.1 CreateTime: 14 July 2013 at 22:23:56 GMT KeyInfo: null) ) saved.
    
        2013-07-14 17:24:50,465 gratia.service(Thread-66) [FINE]: RecordProcessor: 0: ProbeDetails 31 / 31
        (pbs-lsf:fermicloud101.fnal.gov, recordId= Record 
        (Id: fermicloud101.fnal.gov:4549.0 CreateTime: 14 July 2013 at 22:24:19 GMT KeyInfo: null) ) saved. """



        SearchPattern = '.*' + 'RecordProcessor: 0: ProbeDetails' + '.*' + '/' + '.*' + ProbePattern + '.*' + 'saved'
        core.log_message('SearchPattern is:' + str(SearchPattern))
        line, gap = core.monitor_file(core.config['gratia.log.file'], core.state['gratia.log.stat'], SearchPattern, 60.0)
        if(line is not None):
                core.log_message('Gratia processed probe data - Time taken is %.1f seconds' % gap)
                core.log_message('Gratia processed probe data - Line is ' + str(line))
                return True
        else:
            return False

    def isProbeDataValidInDatabase(self, command, queryFailureString, assertionValue='', atLeastOneRecord=False):
        """This helper method queries the database for probe related information and based on the passed-in
     data, determines if the queried information is valid or not."""

        status, stdout, _ = core.system(command, shell=True)
        if(status != 0):
            core.log_message(queryFailureString)
            return False #Unable to query the database
        
        ######If we reached this point, database query was successful. Now, it's time to examine the query output#####
        if (assertionValue != ''): 
            result = re.search(assertionValue, stdout, re.IGNORECASE)
            if(result != None):
                return True #Found the assertionValue in the database
            else:
                return False #Unable to find the assertionValue in the database
            
        else: #No assertionValue passed in
            if(atLeastOneRecord == True):
                if(int(stdout) < 1):
                    core.log_message("Query should return at least ONE record !")
                    return False #Query should return at least one record
                else:
                    return True #Query returned at least one record
            else: #"atLeastOneRecord" Flag was not passed in
                return True 
        
    #This test tries to launch a gratia admin webpage
    def test_01_gratia_admin_webpage (self):
        core.skip_ok_unless_installed('gratia-service')
        host = core.get_hostname()
        admin_webpage = 'http://' + host + ':8880/gratia-administration/status.html?wantDetails=0'
        command = ('curl', admin_webpage)
        core.check_system(command, 'Unable to launch gratia admin webpage')
        
    #This test counts the number of lines in the "show databases" command output
    def test_02_show_databases(self):

        core.skip_ok_unless_installed('gratia-service')    
        command = "echo \"show databases;" + core.config['gratia.sql.querystring'] + "| wc -l",
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to install Gratia Database !', '3'), 'Unable to install Gratia Database !')       

    #This test counts the number of lines in the gratia database tables output
    def test_03_show_gratia_database_tables(self):
        core.skip_ok_unless_installed('gratia-service')     
        command = "echo \"use gratia;show tables;" + core.config['gratia.sql.querystring'] + "| wc -l",
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to install Gratia Database !', '81'), 'Unable to install Gratia Database !')       
        
    #This test customizes /etc/gratia/gridftp-transfer/ProbeConfig file
    def test_04_modify_gridftptransfer_probeconfig(self):

        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer', 'gratia-service')
        probeconfig = core.config['gratia.config.dir'] + "/gridftp-transfer/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        
    #This test copies the necessary files for gridftp test
    def test_05_copy_gridftp_logs(self):

        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer', 'gratia-service')
        core.state['gratia.gridftp-logs-copied'] = False
        self.assert_(self.copy_probe_logs(), "gridftp log copy failed !")
        core.state['gratia.gridftp-logs-copied'] = True


    #This test executes the GridftpTransferProbeDriver
    def test_06_execute_gridftptransfer_probedriver(self):
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer', 'gratia-service')
        core.state['gratia.gridftp-transfer-running'] = False
        self.skip_bad_if(core.state['gratia.gridftp-logs-copied'] == False)
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = os.stat(core.config['gratia.log.file'])
            core.log_message('stat.st_ino is: ' + str(core.state['gratia.log.stat'].st_ino))
            core.log_message('stat.st_size is: ' + str(core.state['gratia.log.stat'].st_size))
        command = ('/usr/share/gratia/gridftp-transfer/GridftpTransferProbeDriver',)
        core.check_system(command, 'Unable to execute GridftpTransferProbeDriver!')
        core.config['gratia.gridftp-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.gridftp-transfer" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.gridftp-temp-dir'])
            self.assert_(result, 'gridftp-transfer outbox check failed !')
        core.state['gratia.gridftp-transfer-running'] = True
        
    #This test checks the database after the successful execution of GridftpTransferProbeDriver
    def test_07_checkdatabase_gridftptransfer_probedriver(self):

        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer', 'gratia-service')
        self.skip_bad_if(core.state['gratia.gridftp-transfer-running'] == False)   
                       
        self.assertEqual(True, self.isProbeInfoProcessed('gridftp-transfer'), 'Sentinel signifying Probe Information was processed NOT found !')
        
        command = "echo \"use gratia; select sum(Njobs) from MasterTransferSummary;" + core.config['gratia.sql.querystring'],
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to query Gratia Database MasterTransferSummary table !', atLeastOneRecord=True), 'Failed Probe Data Validation in Database !')       
        
        command = "echo \"use gratia; select sum(TransferSize) from MasterTransferSummary;" + core.config['gratia.sql.querystring'],        
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to query Gratia Database MasterTransferSummary table !', atLeastOneRecord=True), 'Failed Probe Data Validation in Database !')       

    #This test customizes /etc/gratia/glexec/ProbeConfig file
    def test_08_modify_glexec_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-glexec', 'gratia-service')
        probeconfig = core.config['gratia.config.dir'] + "/glexec/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        self.patternreplace(probeconfig, "gLExecMonitorLog", "gLExecMonitorLog=\"/var/log/glexec.log\"")

    #This test copies glexec.log file from SVN to /var/log
    def test_09_copy_glexec_logs(self):
        core.skip_ok_unless_installed('gratia-probe-glexec', 'gratia-service')
        core.state['gratia.glexec-logs-copied'] = False
        glexec_log =  '/usr/share/osg-test/glexec.log'
        dst_dir = '/var/log'
        self.assert_(self.copy_probe_logs(glexec_log, dst_dir), "glexec log copy failed !")
        core.state['gratia.glexec-logs-copied'] = True

    #This test executes glexec_meter
    def test_10_execute_glexec_meter(self):
        core.skip_ok_unless_installed('gratia-probe-glexec', 'gratia-service')
        core.state['gratia.glexec_meter-running'] = False
        self.skip_bad_if(core.state['gratia.glexec-logs-copied'] == False)
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = os.stat(core.config['gratia.log.file'])
            core.log_message('stat.st_ino is: ' + str(core.state['gratia.log.stat'].st_ino))
            core.log_message('stat.st_size is: ' + str(core.state['gratia.log.stat'].st_size))   
        command = ('/usr/share/gratia/glexec/glexec_meter',)
        core.check_system(command, 'Unable to execute glexec_meter!')      
        core.config['gratia.glexec-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.glexec" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.glexec-temp-dir'])
            self.assert_(result, 'glexec_meter outbox check failed !')
        core.state['gratia.glexec_meter-running'] = True
        
    #This test checks the database after the successful execution of glexec_meter
    def test_11_checkdatabase_glexec_meter(self):
        core.skip_ok_unless_installed('gratia-probe-glexec', 'gratia-service')
        self.skip_bad_if(core.state['gratia.glexec_meter-running'] == False)        
        
        self.assertEqual(True, self.isProbeInfoProcessed('glexec'), 'Sentinel signifying Probe Information was processed NOT found !')

        command = "echo \"use gratia; select Njobs from MasterSummaryData where ProbeName like 'glexec%';" + core.config['gratia.sql.querystring'],
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to query Gratia Database MasterSummaryData table !', '4'), 'Failed Probe Data Validation in Database !')       
        
        command = "echo \"use gratia; select WallDuration from MasterSummaryData where ProbeName like 'glexec%';" + core.config['gratia.sql.querystring'],
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to query Gratia Database MasterSummaryData table !', '302'), 'Failed Probe Data Validation in Database !')       

    #This test customizes /etc/gratia/dCache-storage/ProbeConfig file
    def test_12_modify_dcache_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage', 'gratia-service')
        probeconfig = core.config['gratia.config.dir'] + "/dCache-storage/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        self.patternreplace(probeconfig, "InfoProviderUrl", "InfoProviderUrl=\"http://fndca3a.fnal.gov:2288/info\"")

    #This test copies logs for dcache probe
    def test_13_copy_dcache_logs(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage', 'gratia-service')
        core.state['gratia.dcache-logs-copied'] = False
        self.assert_(self.copy_probe_logs(), "dcache log copy failed !")
        core.state['gratia.dcache-logs-copied'] = True

    #This test executes dCache-storage
    def test_14_execute_dcache_storage(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage', 'gratia-service')
        core.state['gratia.dcache-storage-running'] = False
        self.skip_bad_if(core.state['gratia.dcache-logs-copied'] == False)
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = os.stat(core.config['gratia.log.file'])
            core.log_message('stat.st_ino is: ' + str(core.state['gratia.log.stat'].st_ino))
            core.log_message('stat.st_size is: ' + str(core.state['gratia.log.stat'].st_size))
        command = ('/usr/share/gratia/dCache-storage/dCache-storage_meter.cron.sh',)
        core.check_system(command, 'Unable to execute dCache-storage!')
        core.config['gratia.dcache-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.dCache-storage" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.dcache-temp-dir'])
            self.assert_(result, 'dCache-storage outbox check failed !')
        core.state['gratia.dcache-storage-running'] = True
    
    
    #This test checks the database after the successful execution of dCache-storage
    def test_15_checkdatabase_dcache_storage(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage', 'gratia-service')
        self.skip_bad_if(core.state['gratia.dcache-storage-running'] == False)   
               
        self.assertEqual(True, self.isProbeInfoProcessed('dCache-storage'), 'Sentinel signifying Probe Information was processed NOT found !')
        
        command = "echo \"use gratia; select TotalSpace from StorageElementRecord where ProbeName like 'dCache-storage%';" + core.config['gratia.sql.querystring'],
        status, TotalSpace, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database TotalSpace from StorageElementRecord table !')

        command = "echo \"use gratia; select FreeSpace from StorageElementRecord where ProbeName like 'dCache-storage%';" + core.config['gratia.sql.querystring'],
        status, FreeSpace, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database FreeSpace from StorageElementRecord table !')
        
        command = "echo \"use gratia; select UsedSpace from StorageElementRecord where ProbeName like 'dCache-storage%';" + core.config['gratia.sql.querystring'],
        status, UsedSpace, _ = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to query Gratia Database UsedSpace from StorageElementRecord table !')
        
        #Need to assert only after converting string to long...
        self.assert_(long(TotalSpace) == (long(FreeSpace) + long(UsedSpace)))
        
    #This test customizes /etc/gratia/condor/ProbeConfig file
    def test_16_modify_condor_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-condor', 'gratia-service')  
        probeconfig = core.config['gratia.config.dir'] + "/condor/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        
    #This test copies condor probe related files from SVN to /var/log
    def test_17_copy_condor_logs(self):
        core.skip_ok_unless_installed('gratia-probe-condor', 'gratia-service')  
        core.state['gratia.condor-logs-copied'] = False
        self.assert_(self.copy_probe_logs(), "condor log copy failed !")
        core.state['gratia.condor-logs-copied'] = True
        
    #This test executes condor_meter
    def test_18_execute_condor_meter(self):
        core.skip_ok_unless_installed('gratia-probe-condor', 'gratia-service')  
        core.state['gratia.condor-meter-running'] = False
        self.skip_bad_if(core.state['gratia.condor-logs-copied'] == False)
        self.skip_ok_if(core.state['condor.running-service'] == False, 'Need to have condor service running !')
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = os.stat(core.config['gratia.log.file'])
            core.log_message('stat.st_ino is: ' + str(core.state['gratia.log.stat'].st_ino))
            core.log_message('stat.st_size is: ' + str(core.state['gratia.log.stat'].st_size))       
        command = ('/usr/share/gratia/condor/condor_meter',)
        core.check_system(command, 'Unable to execute condor_meter !')    
        core.config['gratia.condor-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.condor" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.condor-temp-dir'])
            self.assert_(result, 'condor outbox check failed !')
        core.state['gratia.condor-meter-running'] = True

    #This test checks database after condor_meter is run
    def test_19_checkdatabase_condor_meter(self):
        core.skip_ok_unless_installed('gratia-probe-condor', 'gratia-service')  
        self.skip_bad_if(core.state['gratia.condor-meter-running'] == False, 'Need to have condor-meter running !')           
        
        self.assertEqual(True, self.isProbeInfoProcessed('condor'), 'Sentinel signifying Probe Information was processed NOT found !')
   
        command = "echo \"use gratia; select sum(Njobs) from MasterSummaryData where ProbeName like 'condor%';" + core.config['gratia.sql.querystring'],
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to query Gratia Database Njobs from MasterSummaryData table !', atLeastOneRecord=True), 'Failed Probe Data Validation in Database !')       
        
        command = "echo \"use gratia; select sum(WallDuration) from MasterSummaryData where ProbeName like 'condor%';" + core.config['gratia.sql.querystring'],
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to query WallDuration from MasterSummaryData table !', atLeastOneRecord=True), 'Failed Probe Data Validation in Database !')  
        
    #This test customizes /etc/gratia/psacct/ProbeConfig file
    def test_20_modify_psacct_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-psacct', 'gratia-service')  
        probeconfig = core.config['gratia.config.dir'] + "/psacct/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        self.patternreplace(probeconfig, "Grid=", "Grid=\"Local\"")

    #This test starts the psacct service
    def test_21_start_psacct_service(self):
        core.skip_ok_unless_installed('gratia-probe-psacct', 'gratia-service')  
        service.start('psacct', 'error')
        
    #This test executes psacct
    def test_22_execute_psacct(self):
        core.skip_ok_unless_installed('gratia-probe-psacct', 'gratia-service')  
        core.state['gratia.psacct-running'] = False
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = os.stat(core.config['gratia.log.file'])
            core.log_message('stat.st_ino is: ' + str(core.state['gratia.log.stat'].st_ino))
            core.log_message('stat.st_size is: ' + str(core.state['gratia.log.stat'].st_size))
        command = ('/usr/share/gratia/psacct/psacct_probe.cron.sh',)
        core.check_system(command, 'Unable to execute psacct!')
        core.config['gratia.psacct-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.psacct" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.psacct-temp-dir'])
            self.assert_(result, 'psacct outbox check failed !')
        core.state['gratia.psacct-running'] = True

    #This test checks database after psacct is run
    def test_23_checkdatabase_psacct(self):
        core.skip_ok_unless_installed('gratia-probe-psacct', 'gratia-service')  
        self.skip_bad_if(core.state['gratia.psacct-running'] == False, 'Need to have psacct running !')           
        
        self.assertEqual(True, self.isProbeInfoProcessed('psacct'), 'Sentinel signifying Probe Information was processed NOT found !')
        
        command = "echo \"use gratia; select * from MasterSummaryData where ProbeName like 'psac%' and ResourceType='RawCPU';" + core.config['gratia.sql.querystring'] +  "| wc -l",
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to query MasterSummaryData table !', atLeastOneRecord=True), 'Failed Probe Data Validation in Database !')   

    #This test customizes /etc/gratia/bdii-status/ProbeConfig file
    def test_24_modify_bdii_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-bdii-status', 'gratia-service')  
        probeconfig = core.config['gratia.config.dir'] + "/bdii-status/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        
    #This test executes bdii-status
    def test_25_execute_bdii_status(self):
        core.skip_ok_unless_installed('gratia-probe-bdii-status', 'gratia-service')  
        core.state['gratia.bdii-status-running'] = False
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = os.stat(core.config['gratia.log.file'])
            core.log_message('stat.st_ino is: ' + str(core.state['gratia.log.stat'].st_ino))
            core.log_message('stat.st_size is: ' + str(core.state['gratia.log.stat'].st_size))
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
        
    #This test checks database after bdii-status is run
    def test_26_checkdatabase_bdii_status(self):
        core.skip_ok_unless_installed('gratia-probe-bdii-status', 'gratia-service')  
        self.skip_bad_if(core.state['gratia.bdii-status-running'] == False, 'Need to have gratia-probe-bdii-status running !')           
        
        self.assertEqual(True, self.isProbeInfoProcessed('bdii'), 'Sentinel signifying Probe Information was processed NOT found !')
        
        command = "echo \"use gratia; select count(*) from ComputeElement;" + core.config['gratia.sql.querystring'],
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to query count from ComputeElement table !', atLeastOneRecord=True), 'Failed Probe Data Validation in Database !')   
        
    #This test customizes /etc/gratia/condor/ProbeConfig file
    def test_27_modify_pbs_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf', 'gratia-service')  
        probeconfig = core.config['gratia.config.dir'] + "/pbs-lsf/ProbeConfig"
        self.modify_probeconfig(probeconfig)

    #This test copies pbs probe related logs
    def test_28_copy_pbs_logs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf', 'gratia-service')  
        core.state['gratia.pbs-logs-copied'] = False
        pbs_log = '/usr/share/osg-test/20130603'
        dst_dir = '/var/spool/pbs/server_priv/accounting'
        self.assert_(self.copy_probe_logs(pbs_log, dst_dir), "pbs log copy failed !")
        core.state['gratia.pbs-logs-copied'] = True   

    
    #This test executes pbs probe
    def test_29_execute_pbs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf', 'gratia-service')    
        core.state['gratia.pbs-running'] = False
        self.skip_bad_if(core.state['gratia.pbs-logs-copied'] == False)
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = os.stat(core.config['gratia.log.file'])
            core.log_message('stat.st_ino is: ' + str(core.state['gratia.log.stat'].st_ino))
            core.log_message('stat.st_size is: ' + str(core.state['gratia.log.stat'].st_size))   
        command = ('/usr/share/gratia/pbs-lsf/pbs-lsf_meter.cron.sh',)
        core.check_system(command, 'Unable to execute pbs-lsf_meter !')
        core.config['gratia.pbs-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.pbs-lsf" + core.config['gratia.tmpdir.postfix']
        if(core.state['gratia.database-installed'] == True):
            result = self.isProbeOutboxDirEmpty(core.config['gratia.pbs-temp-dir'])
            self.assert_(result,'pbs outbox check failed !')
        core.state['gratia.pbs-running'] = True

    #This test checks database after pbs is run
    def test_30_checkdatabase_pbs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf', 'gratia-service')  
        self.skip_bad_if(core.state['gratia.pbs-running'] == False, 'Need to have pbs running !')           
        
        self.assertEqual(True, self.isProbeInfoProcessed('pbs-lsf'), 'Sentinel signifying Probe Information was processed NOT found !')
        
        probename="'pbs-lsf:" + core.config['gratia.host']
        query="use gratia; select sum(nJobs) from MasterSummaryData where ProbeName=" + probename + "';"        
        command = "echo " + "\""+ query + core.config['gratia.sql.querystring'],
        
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to query MasterSummaryData table !', '30'), 'Failed Probe Data Validation in Database !') 
