import os
import re
import shutil
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestGratia(osgunittest.OSGTestCase):

    @core.elrelease(6)
    def setUp(self):
        pass

    def patternreplace(self, infile_name, pattern, full_line, insert_after=False):
        """This method is taken from test_28 - we can consider moving it to core.py module
     This helper method loops through the passed in infile line by line.
     If it finds the passed in pattern in a line, it EITHER replaces the whole line
     with the passed in full_line OR inserts it after the line, depending on the
     desired input"""

        infile = open(infile_name, "r")
        outfile_name = infile_name + ".tmp"
        outfile = open(outfile_name, 'w')
        retval = False

        #If the pattern is found in a non-comment line, replace the line with the passed in "full_line"
        for line in infile:
            if pattern in line and not line.startswith('#'):
                if insert_after == False: #Default case, just replace the line
                    line = full_line + "\n"
                else: #Insert the passed in line AFTER the line in which the pattern was found
                    line = line + full_line + "\n"
                retval = True #If the pattern was found, it's a success
            outfile.write(line)
        outfile.close()
        infile.close()

        shutil.move(outfile_name, infile_name)
        return retval


    def copy_user_vo_map_file(self):
        """This helper method copies user-vo-map in /var/lib/osg, if not already present"""

        user_vo_map_dir = '/var/lib/osg/'
        user_vo_map_file = '/usr/share/osg-test/gratia/user-vo-map'
        if not os.path.exists(user_vo_map_dir):
            os.makedirs(user_vo_map_dir)
            try:
                shutil.copy(user_vo_map_file, user_vo_map_dir)
            except IOError as e:
                core.log_message("Unable to copy file. %s" % e)
                return False
        elif not os.path.exists(os.path.join(user_vo_map_dir, 'user-vo-map')):
            # Directory exists, copy file, if the file is not already present
            try:
                shutil.copy(user_vo_map_file, user_vo_map_dir)
            except IOError as e:
                core.log_message("Unable to copy file. %s" % e)
                return False
        else: #both directory and file are present and so, do nothing...
            core.log_message(str(os.listdir(user_vo_map_dir)))
            return True

    def copy_probe_logs(self, log='', logdirectory=''):
        """This helper method copies Probe Logs to the passed in directory"""
        if not 'gratia.user-vo-map' in core.config:
            return False
        else:
            if log != '' and logdirectory != '':
                try:
                    if not os.path.exists(logdirectory):
                        os.makedirs(logdirectory)
                    shutil.copy(log, logdirectory)
                    core.log_message(str(os.listdir(logdirectory)))
                except IOError as e:
                    core.log_message("Unable to copy log. %s" % e)
                    return False
        #If we've reached this far, it's a success
        return True

    def modify_probeconfig(self, probeconfig):
        """This helper method modifies the Probe Configuration, generally needed by many probes"""

        #Backup the existing ProbeConfig, before any modification, so that it can be restored later
        #Note that "owner" has to be a unique string since "ProbeConfig" filename is the same for all probes
        #If ProbeConfig path is: /etc/gratia/gridftp-transfer/ProbeConfig, "owner" = "gridftp-transfer"
        owner = os.path.basename(os.path.dirname(probeconfig))
        files.preserve(probeconfig, owner)

        host = core.get_hostname()
        collectorhost = "    CollectorHost=\"" + host + ":8880\""
        sslhost = "    SSLHost=\"" + host + ":8443\""
        sslregistrationhost = "    SSLRegistrationHost=\"" + host + ":8880\""
        self.patternreplace(probeconfig, "CollectorHost", collectorhost)
        self.patternreplace(probeconfig, "SSLHost", sslhost)
        self.patternreplace(probeconfig, "SSLRegistrationHost", sslregistrationhost)
        self.patternreplace(probeconfig, "SiteName", "SiteName=\"OSG Test site\"")
        self.patternreplace(probeconfig, "EnableProbe", "EnableProbe=\"1\"")
        #If a line with QuarantineUnknownVORecords pattern is not found, insert it after QuarantineSize line
        if self.patternreplace(probeconfig, "QuarantineUnknownVORecords=", "QuarantineUnknownVORecords=\"0\"") == False:
            self.patternreplace(probeconfig, "QuarantineSize=", "QuarantineUnknownVORecords=\"0\"", insert_after=True)

    def isProbeOutboxDirEmpty(self, gratiaProbeTempDir):
        """This helper method returns True if the outbox directory for the probe, is empty; False otherwise"""
        outboxdir = gratiaProbeTempDir + "/outbox/"
        try:
            core.log_message('isProbeOutboxDirEmpty method - outboxdir is: ' + str(outboxdir))
            if not os.listdir(outboxdir):
                return True
            else:
                return False
        except OSError:
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

        2013-07-14 17:23:18,294 gratia.service(Thread-66) [FINE]: RecordProcessor: 0: ProbeDetails 2 / 2
        (condor:fermicloud101.fnal.gov, recordId= Record
        (Id: fermicloud101.fnal.gov:3390.0 CreateTime: 14 July 2013 at 22:22:48 GMT KeyInfo: null) ) saved.

        2013-07-14 17:24:50,465 gratia.service(Thread-66) [FINE]: RecordProcessor: 0: ProbeDetails 31 / 31
        (pbs-lsf:fermicloud101.fnal.gov, recordId= Record
        (Id: fermicloud101.fnal.gov:4549.0 CreateTime: 14 July 2013 at 22:24:19 GMT KeyInfo: null) ) saved. """



        record_re = '.*' + 'RecordProcessor: 0: ProbeDetails' + '.*' + '/' + '.*' + ProbePattern + '.*' + 'saved'
        line, gap = core.monitor_file(core.config['gratia.log.file'], core.state['gratia.log.stat'], record_re, 600.0)
        if line is not None:
            core.log_message('Gratia processed probe data - Time taken is %.1f seconds' % gap)
            core.log_message('Gratia processed probe data - Line is ' + str(line))
            return True
        else:
            core.log_message('Did not find the search pattern within the given time limit.')
            return False

    def isProbeDataValidInDatabase(self, command, queryFailureString, assertionValue='', atLeastOneRecord=False):
        """This helper method queries the database for probe related information and based on the passed-in
     data, determines if the queried information is valid or not."""

        status, stdout, _ = core.system(command, shell=True)
        if status != 0:
            core.log_message(queryFailureString)
            return False #Unable to query the database

        ######If we reached this point, database query was successful. Now, it's time to examine the query output#####
        if assertionValue != '':
            result = re.search(assertionValue, stdout, re.IGNORECASE)
            if result != None:
                return True #Found the assertionValue in the database
            else:
                return False #Unable to find the assertionValue in the database

        else: #No assertionValue passed in
            if atLeastOneRecord == True:
                if int(stdout) < 1:
                    core.log_message("Query did not return one or more records.")
                    return False #Query should return at least one record
                else:
                    return True #Query returned at least one record
            else: #"atLeastOneRecord" Flag was not passed in
                return True

    #This test tries to launch a gratia admin webpage
    def test_01_gratia_admin_webpage (self):
        core.skip_ok_unless_installed('gratia-service')
        self.skip_bad_unless(core.state['tomcat.started'], 'Tomcat not started')
        host = core.get_hostname()
        admin_webpage = 'http://' + host + ':8880/gratia-administration/status.html?wantDetails=0'
        command = ('curl', admin_webpage)
        core.check_system(command, 'Unable to launch gratia admin webpage')

    #This test counts the number of lines in the "show databases" command output
    def test_02_show_databases(self):
        core.skip_ok_unless_installed('gratia-service')
        command = "echo \"show databases;" + core.config['gratia.sql.querystring'] + "| wc -l",
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to install Gratia Database.', '3'),
                         'Unable to install Gratia Database.')

    #This test counts the number of lines in the gratia database tables output
    def test_03_show_gratia_database_tables(self):
        core.skip_ok_unless_installed('gratia-service')
        command = "echo \"use gratia_osgtest;show tables;" + core.config['gratia.sql.querystring'] + "| wc -l",
        if core.PackageVersion('gratia-service') >= '1.16.3':
            expected_table_count = '82'
        else:
            expected_table_count = '81'
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, 'Unable to install Gratia Database.',
                                                               expected_table_count),
                         'Unable to install Gratia Database.')

    #This test customizes /etc/gratia/gridftp-transfer/ProbeConfig file
    def test_04_modify_gridftptransfer_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer', 'gratia-service')
        probeconfig = core.config['gratia.config.dir'] + "/gridftp-transfer/ProbeConfig"
        self.modify_probeconfig(probeconfig)

    #This test copies the necessary files for gridftp test
    def test_05_copy_gridftp_logs(self):
        core.state['gratia.gridftp-logs-copied'] = False
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer', 'gratia-service')
        self.assert_(self.copy_probe_logs(), "gridftp log copy failed.")
        core.state['gratia.gridftp-logs-copied'] = True


    #This test executes the gridftp-transfer probe
    def test_06_execute_gridftptransfer_probedriver(self):
        core.state['gratia.gridftp-transfer-running'] = False
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer', 'gratia-service', 'globus-gridftp-server-progs',
                                      'globus-ftp-client', 'globus-proxy-utils', 'globus-gass-copy-progs')
        self.skip_ok_unless(core.state['gridftp.started-server'], 'gridftp server not running')
        self.skip_bad_unless(core.state['gratia.gridftp-logs-copied'], 'gridftp logs not copied')
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = core.get_stat(core.config['gratia.log.file'])
            core.log_message('stat.st_ino is: ' + str(core.state['gratia.log.stat'].st_ino))
            core.log_message('stat.st_size is: ' + str(core.state['gratia.log.stat'].st_size))
        if core.PackageVersion('gratia-probe-gridftp-transfer') >= '1.17.0-1':
            probe_script = 'gridftp-transfer_meter'
        else:
            probe_script = 'GridftpTransferProbeDriver'
        command = ('/usr/share/gratia/gridftp-transfer/%s' % probe_script,)
        core.check_system(command, 'Unable to execute %s.' % probe_script)
        core.config['gratia.gridftp-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.gridftp-transfer" + \
                                                 core.config['gratia.tmpdir.postfix']
        if core.state['gratia.database-installed'] == True:
            result = self.isProbeOutboxDirEmpty(core.config['gratia.gridftp-temp-dir'])
            self.assert_(result, 'gridftp-transfer outbox check failed.')
        core.state['gratia.gridftp-transfer-running'] = True

    #This test checks the database after the successful execution of the gridftp-transfer probe
    def test_07_checkdatabase_gridftptransfer_probedriver(self):
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer', 'gratia-service')
        self.skip_bad_if(core.state['gratia.gridftp-transfer-running'] == False, 'gridftp transfer probe not running')

        self.assertEqual(True, self.isProbeInfoProcessed('gridftp-transfer'),
                         'Sentinel signifying that Probe Information was processed NOT found.')

        command = "echo \"use gratia_osgtest; select sum(Njobs) from MasterTransferSummary;" + \
                  core.config['gratia.sql.querystring'],
        probe_validation_msg = 'Unable to query Gratia Database MasterTransferSummary table'
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, probe_validation_msg, atLeastOneRecord=True),
                         'Failed Probe Data Validation in Database.')

        command = "echo \"use gratia_osgtest; select sum(TransferSize) from MasterTransferSummary;" + \
                  core.config['gratia.sql.querystring'],
        self.assertEqual(True, self.isProbeDataValidInDatabase(command, probe_validation_msg, atLeastOneRecord=True),
                         'Failed Probe Data Validation in Database.')

    #This test customizes /etc/gratia/condor/ProbeConfig file
    def test_16_modify_condor_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-condor', 'gratia-service')
        probeconfig = core.config['gratia.config.dir'] + "/condor/ProbeConfig"
        self.modify_probeconfig(probeconfig)

    #This test copies condor probe related files from SVN to /var/log
    def test_17_copy_condor_logs(self):
        core.skip_ok_unless_installed('gratia-probe-condor', 'gratia-service')
        core.state['gratia.condor-logs-copied'] = False
        self.assert_(self.copy_probe_logs(), "condor log copy failed.")
        core.state['gratia.condor-logs-copied'] = True

    #This test executes condor_meter
    def test_18_execute_condor_meter(self):
        core.state['gratia.condor-meter-running'] = False
        core.skip_ok_unless_installed('gratia-probe-condor', 'gratia-service', 'htcondor-ce-condor')
        self.skip_bad_if(core.state['gratia.condor-logs-copied'] == False)
        self.skip_bad_unless(core.state['condor-ce.started-service'],
                             'condor-ce not running')
        self.skip_bad_unless(core.state['condor.running-service'], message='Condor service not running')
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = core.get_stat(core.config['gratia.log.file'])
            core.log_message('stat.st_ino is: ' + str(core.state['gratia.log.stat'].st_ino))
            core.log_message('stat.st_size is: ' + str(core.state['gratia.log.stat'].st_size))
        command = ('/usr/share/gratia/condor/condor_meter',)
        core.check_system(command, 'Unable to execute condor_meter.')
        core.config['gratia.condor-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.condor" + \
                                                core.config['gratia.tmpdir.postfix']
        if core.state['gratia.database-installed'] == True:
            result = self.isProbeOutboxDirEmpty(core.config['gratia.condor-temp-dir'])
            self.assert_(result, 'condor outbox check failed.')
        core.state['gratia.condor-meter-running'] = True

    #This test checks database after condor_meter is run
    def test_19_checkdatabase_condor_meter(self):
        core.skip_ok_unless_installed('gratia-probe-condor', 'gratia-service')
        self.skip_bad_if(core.state['gratia.condor-meter-running'] == False, 'Condor-meter is not running.')

        self.assertEqual(True, self.isProbeInfoProcessed('condor'),
                         'Sentinel signifying that Probe Information was processed NOT found.')

        command = "echo \"use gratia_osgtest; " + \
                  "select sum(Njobs) from MasterSummaryData where ProbeName like 'condor%';" + \
                  core.config['gratia.sql.querystring'],
        self.assertEqual(True, self.isProbeDataValidInDatabase(command,
                                                               'Unable to query Gratia Database Njobs from MasterSummaryData table.',
                                                               atLeastOneRecord=True),
                         'Failed Probe Data Validation in Database.')

        command = "echo \"use gratia_osgtest; " + \
                  "select sum(WallDuration) from MasterSummaryData where ProbeName like 'condor%';" + \
                  core.config['gratia.sql.querystring'],
        self.assertEqual(True, self.isProbeDataValidInDatabase(command,
                                                               'Unable to query WallDuration from MasterSummaryData table.',
                                                               atLeastOneRecord=True),
                         'Failed Probe Data Validation in Database.')

    #This test customizes /etc/gratia/condor/ProbeConfig file
    def test_20_modify_pbs_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf', 'gratia-service')
        probeconfig = core.config['gratia.config.dir'] + "/pbs-lsf/ProbeConfig"
        self.modify_probeconfig(probeconfig)

    #This test copies pbs probe related logs
    def test_21_copy_pbs_logs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf', 'gratia-service')
        core.state['gratia.pbs-logs-copied'] = False
        pbs_log = '/usr/share/osg-test/gratia/20130603'
        dst_dir = '/var/spool/pbs/server_priv/accounting'
        self.assert_(self.copy_probe_logs(pbs_log, dst_dir), "pbs log copy failed.")
        core.state['gratia.pbs-logs-copied'] = True

    #This test executes pbs probe
    def test_22_execute_pbs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf', 'gratia-service')
        core.state['gratia.pbs-running'] = False
        self.skip_bad_if(core.state['gratia.pbs-logs-copied'] == False)
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = core.get_stat(core.config['gratia.log.file'])
            core.log_message('stat.st_ino is: ' + str(core.state['gratia.log.stat'].st_ino))
            core.log_message('stat.st_size is: ' + str(core.state['gratia.log.stat'].st_size))
        command = ('/usr/share/gratia/pbs-lsf/pbs-lsf_meter.cron.sh',)
        core.check_system(command, 'Unable to execute pbs-lsf_meter.')
        core.config['gratia.pbs-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.pbs-lsf" + \
                                             core.config['gratia.tmpdir.postfix']
        if core.state['gratia.database-installed'] == True:
            result = self.isProbeOutboxDirEmpty(core.config['gratia.pbs-temp-dir'])
            self.assert_(result, 'pbs outbox check failed.')
        core.state['gratia.pbs-running'] = True

    #This test checks database after pbs is run
    def test_23_checkdatabase_pbs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf', 'gratia-service')
        self.skip_bad_if(core.state['gratia.pbs-running'] == False, 'Need to have pbs running.')

        self.assertEqual(True, self.isProbeInfoProcessed('pbs-lsf'),
                         'Sentinel signifying that Probe Information was processed NOT found.')

        probename = "'pbs-lsf:" + core.config['gratia.host']
        query = "use gratia_osgtest; select sum(nJobs) from MasterSummaryData where ProbeName=" + probename + "';"
        command = "echo " + "\""+ query + core.config['gratia.sql.querystring'],

        self.assertEqual(True, self.isProbeDataValidInDatabase(command,
                                                               'Unable to query MasterSummaryData table.',
                                                               '30'),
                         'Failed Probe Data Validation in Database.')

    def test_24_modify_sge_probeconfig(self):
        core.skip_ok_unless_installed('gratia-probe-sge', 'gratia-service')
        probeconfig = core.config['gratia.config.dir'] + "/sge/ProbeConfig"
        self.modify_probeconfig(probeconfig)
        self.patternreplace(probeconfig, "SGEAccountingFile=\"\"", "SGEAccountingFile=\"/var/log/accounting\"")

    def test_25_copy_sge_logs(self):
        core.skip_ok_unless_installed('gratia-probe-sge', 'gratia-service')
        core.state['gratia.sge-logs-copied'] = False
        sge_log = '/usr/share/osg-test/gratia/accounting'
        dst_dir = '/var/log'
        self.assert_(self.copy_probe_logs(sge_log, dst_dir), "sge log copy failed.")
        core.state['gratia.sge-logs-copied'] = True

    def test_26_execute_sge(self):
        core.skip_ok_unless_installed('gratia-probe-sge', 'gratia-service')
        core.state['gratia.sge-running'] = False
        self.skip_bad_if(core.state['gratia.sge-logs-copied'] == False)
        if os.path.exists(core.config['gratia.log.file']):
            core.state['gratia.log.stat'] = core.get_stat(core.config['gratia.log.file'])
            core.log_message('stat.st_ino is: ' + str(core.state['gratia.log.stat'].st_ino))
            core.log_message('stat.st_size is: ' + str(core.state['gratia.log.stat'].st_size))
        command = ('/usr/share/gratia/sge/sge_meter.cron.sh',)
        core.check_system(command, 'Unable to execute sge_meter.')
        core.config['gratia.sge-temp-dir'] = core.config['gratia.tmpdir.prefix'] + "subdir.sge" + \
                                             core.config['gratia.tmpdir.postfix']
        if core.state['gratia.database-installed'] == True:
            result = self.isProbeOutboxDirEmpty(core.config['gratia.sge-temp-dir'])
            self.assert_(result, 'sge outbox check failed.')
        core.state['gratia.sge-running'] = True

    def test_27_checkdatabase_sge(self):
        core.skip_ok_unless_installed('gratia-probe-sge', 'gratia-service')
        self.skip_bad_if(core.state['gratia.sge-running'] == False, 'Need to have sge running.')
        self.assertEqual(True, self.isProbeInfoProcessed('sge'),
                         'Sentinel signifying that Probe Information was processed NOT found.')
        probename = "'sge:" + core.config['gratia.host']
        query = "use gratia_osgtest; select sum(nJobs) from MasterSummaryData where ProbeName=" + probename + "';"
        command = "echo " + "\""+ query + core.config['gratia.sql.querystring'],
        self.assertEqual(True, self.isProbeDataValidInDatabase(command,
                                                               'Unable to query Gratia Database MasterSummaryData table.',
                                                               atLeastOneRecord=True),
                         'Failed Probe Data Validation in Database.')
