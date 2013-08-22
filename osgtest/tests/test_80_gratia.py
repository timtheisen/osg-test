import os
import shutil
import time
import datetime
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service


class TestStopGratia(osgunittest.OSGTestCase):

    def remove_cert(self, target_key):
        """remove_cert has been taken from test_78_voms.py
     We should consider putting this code in the core library
     Carefully removes a certificate with the given key.  Removes all
     paths associated with the key, as created by the install_cert()
     function."""

        if core.state.has_key(target_key):
            os.remove(core.state[target_key])
        if core.state.has_key(target_key + '-backup'):
            shutil.move(core.state[target_key + '-backup'],
                        core.state[target_key])
        if core.state.has_key(target_key + '-dir'):
            target_dir = core.state[target_key + '-dir']
            if len(os.listdir(target_dir)) == 0:
                os.rmdir(target_dir)

    #This test removes the http certificates, if not already removed earlier
    def test_01_remove_certs(self):

        core.skip_ok_unless_installed('gratia-service')
        #The following code can be uncommented for troubleshooting purposes
        #utc_datetime = datetime.datetime.utcnow()
        #formated_string = utc_datetime.strftime("%Y-%m-%d-%H%MZ") #Result: '2011-12-12-0939Z'
        #gratia_log_current = '/var/log/gratia-service/gratia.log'
        #gratia_log_archive = '/root/gratia_logs' +'/gratia_log_%s.txt'% formated_string
        #shutil.copy2(gratia_log_current, gratia_log_archive)
        if(core.state.has_key('gratia.save-logs') == True):
            try:
                gratia_service_log_string = files.read('/var/log/gratia-service/gratia.log', as_single_string=True)
                core.log_message("\n%%%%%START_GRATIA_SERVICE_LOG%%%%%\n" + str(gratia_service_log_string))
                core.log_message("\n%%%%%END_GRATIA_SERVICE_LOG%%%%%\n")

                utc_datetime = datetime.datetime.utcnow()
                date_string = utc_datetime.strftime("%Y-%m-%d") #Sample Result: '2013-08-21'
                gratia_dated_log = '/var/log/gratia/' + date_string + '.log'
                gratia_dated_log_string = files.read(gratia_dated_log, as_single_string=True)
                core.log_message("\n%%%%%START_GRATIA_DATED_LOG%%%%%\n" + str(gratia_dated_log_string))
                core.log_message("\n%%%%%END_GRATIA_DATED_LOG%%%%%\n")
            except Exception, e:
                core.log_message("Unable to save gratia logs ! Ignoring this error, beyond logging this message..." + str(e))

        self.skip_ok_if(core.state['voms.removed-certs'] == True, 'Certs were already removed')
        # Do the keys first, so that the directories will be empty for the certs.
        self.remove_cert('certs.httpkey')
        self.remove_cert('certs.httpcert')

    #This test drops the gratia database
    def test_02_uninstall_gratia_database(self):

        core.skip_ok_unless_installed('gratia-service')    
       
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        contents="[client]\n" + "password=\n"
        files.write(filename, contents, backup=False)
        
        #Command to drop the gratia database is:
        #echo "drop database gratia;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" -B --unbuffered  --user=root --port=3306         
        command = "echo \"drop database gratia;\" | mysql --defaults-extra-file=\"" + filename + "\" -B --unbuffered  --user=root --port=3306"
        core.check_system(command, 'Unable to drop Gratia Database !', shell=True)
        files.remove(filename)
        #At this time, remove the gratia reader password file also
        files.remove(core.config['gratia.sql.file'])
        
    #This test cleans up the appropriate gratia directory
    def test_03_cleanup_etcgratia_directory(self):

        core.skip_ok_unless_installed('gratia-service')
        directory = core.config['gratia.config.dir'] + "/" + core.config['gratia.directory']
        files.remove(directory, True)
        
    #This test cleans up gridftp related files
    def test_04_cleanup_gridftp(self):

        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer', 'gratia-service')
        try:
            files.remove("/var/lib/gratia/tmp/GridftpAccountingProbeState")
            files.remove("/var/log/gridftp.log")
            files.remove("/var/log/gridftp-auth.log")
            if 'gratia.gridftp-temp-dir' in core.config:
                files.remove(core.config['gratia.gridftp-temp-dir'], True)
            files.remove(core.config['gratia.config.dir'] + "/gridftp-transfer", True)
        except OSError, e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise

    #This test cleans up glexec related files
    def test_05_cleanup_glexec(self):

        core.skip_ok_unless_installed('gratia-probe-glexec', 'gratia-service')
        try:
            files.remove("/var/lib/gratia/tmp/GlexecAccountingProbeState")
            files.remove("/var/log/glexec.log")
            files.remove("/var/lib/gratia/data/glexec_plugin.chk")

            if 'gratia.glexec-temp-dir' in core.config:
                files.remove(core.config['gratia.glexec-temp-dir'], True)
            files.remove(core.config['gratia.config.dir'] + "/glexec", True)
        except OSError, e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise
        
    #This test cleans up dcache related files
    def test_06_cleanup_dcache(self):

        core.skip_ok_unless_installed('gratia-probe-dcache-storage', 'gratia-service')
        try:
            files.remove("/var/lib/gratia/tmp/dCache-storage_meter.cron.pid")
            if 'gratia.dcache-temp-dir' in core.config:
                files.remove(core.config['gratia.dcache-temp-dir'], True)
            files.remove(core.config['gratia.config.dir'] + "/dCache-storage", True)
        except OSError, e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise

    #This test cleans up condor related files
    def test_07_cleanup_condor(self):
        core.skip_ok_unless_installed('gratia-probe-condor', 'gratia-service')
        try:
            files.remove("/var/lib/gratia/data/gratia_certinfo_condor*")
            files.remove("/var/lib/gratia/data/history.1211*")
            if 'gratia.condor-temp-dir' in core.config:
                files.remove(core.config['gratia.condor-temp-dir'], True)
            files.remove(core.config['gratia.config.dir'] + "/condor", True)
        except OSError, e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise
        
    #This test stops psacct service
    def test_08_stop_psacct_service(self):
        core.skip_ok_unless_installed('psacct', 'gratia-probe-psacct', 'gratia-service')
        command = ('/etc/init.d/psacct', 'stop')
        core.check_system(command, 'Unable to stop psacct!')

    #This test cleans up psacct related files
    def test_09_cleanup_psacct(self):
        core.skip_ok_unless_installed('psacct', 'gratia-probe-psacct', 'gratia-service')
        try:
            files.remove("/var/lib/gratia/account/pacct")
            files.remove("/var/lib/gratia/account/pacct.creation")
            files.remove("/var/lib/gratia/backup/*")
            if 'gratia.psacct-temp-dir' in core.config:
                files.remove(core.config['gratia.psacct-temp-dir'], True)
            files.remove(core.config['gratia.config.dir'] + "/psacct", True)
        except OSError, e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise

    #This test cleans up bdii related files
    def test_10_cleanup_bdii(self):
        core.skip_ok_unless_installed('gratia-probe-bdii-status', 'gratia-service')
        try:
            if 'gratia.bdii-temp-dir' in core.config:
                #resorting to shell remove command due to wildcharacter in the name       
                command = ('rm', '-rf', core.config['gratia.bdii-temp-dir'])
                core.check_system(command, 'Unable to clean up core.config[\'gratia.bdii-temp-dir\'] !')
            files.remove(core.config['gratia.config.dir'] + "/bdii-status", True)
        except OSError, e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise
        
    #This test cleans up pbs related files
    def test_11_cleanup_pbs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf', 'gratia-service')
        try:
            files.remove("/var/lib/gratia/tmp/urCollectorBuffer.pbs")
            if 'gratia.pbs-temp-dir' in core.config:
                files.remove(core.config['gratia.pbs-temp-dir'], True)
            files.remove("/var/lib/gratia/tmp/urCollector", True)
            files.remove(core.config['gratia.config.dir'] + "/pbs-lsf", True)
            files.remove("/var/lib/gratia/pbs-lsf", True)
            files.remove("/var/spool/pbs/server_priv/accounting", True)
        except OSError, e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise
