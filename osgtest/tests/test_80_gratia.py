import os
import shutil

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStopGratia(osgunittest.OSGTestCase):

#===============================================================================
#remove_cert has been taken from test_78_voms.py
# We should consider putting this code in the core library
#===============================================================================
    # Carefully removes a certificate with the given key.  Removes all
    # paths associated with the key, as created by the install_cert()
    # function.
    def remove_cert(self, target_key):
        if core.state.has_key(target_key):
            os.remove(core.state[target_key])
        if core.state.has_key(target_key + '-backup'):
            shutil.move(core.state[target_key + '-backup'],
                        core.state[target_key])
        if core.state.has_key(target_key + '-dir'):
            target_dir = core.state[target_key + '-dir']
            if len(os.listdir(target_dir)) == 0:
                os.rmdir(target_dir)
                
    #====================================================================================
    # This helper method writes a file with sql credentials and returns back the filename
    #====================================================================================
    def write_sql_credentials_file(self):
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        contents="[client]\n" + "password=reader\n"
        files.write(filename, contents)
        return filename

    #===========================================================================
    # This test removes the http certificates, if not already removed earlier
    #===========================================================================
    def test_01_remove_certs(self):
        core.skip_ok_unless_installed('gratia-service')
        self.skip_ok_if(core.state['voms.removed-certs'] == True, 'Certs were already removed')
        # Do the keys first, so that the directories will be empty for the certs.
        self.remove_cert('certs.httpkey')
        self.remove_cert('certs.httpcert')

    #===========================================================================
    # This test drops the gratia database
    #===========================================================================
    def test_02_uninstall_gratia_database(self):
        core.skip_ok_unless_installed('gratia-service')    
       
        filename = self.write_sql_credentials_file()
        
        #Command to drop the gratia database is:
        #echo "drop database gratia;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" -B --unbuffered  --user=root --port=3306         
        command = "echo \"drop database gratia;\" | mysql --defaults-extra-file=\"" + filename + "\" -B --unbuffered  --user=root --port=3306"
        core.check_system(command, 'Unable to drop Gratia Database !', shell=True)
        files.remove(filename)
        
    #===========================================================================
    # This test cleans up the appropriate gratia directory
    #===========================================================================
    def test_03_cleanup_etcgratia_directory(self):
        core.skip_ok_unless_installed('gratia-service')
        directory = core.config['gratia.config.dir'] + "/" + core.config['gratia.directory']
        #files.remove doesn't remove non-empty directories. In such a case, use shutil.rmtree command
        try:
            files.remove(directory)
        except:
            shutil.rmtree(directory)
        
    #==========================================
    # This test cleans up gridftp related files 
    #==========================================
    def test_04_cleanup_gridftp(self):
        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer')
        files.remove("/var/lib/gratia/tmp/GridftpAccountingProbeState")
        files.remove("/var/log/gridftp.log")
        files.remove("/var/log/gridftp-auth.log")
        #files.remove doesn't remove non-empty directories. In such a case, use shutil.rmtree command
        try:
            files.remove(core.config['gratia.gridftp-temp-dir'])
            files.remove(core.config['gratia.config.dir'] + "/gridftp-transfer")
        except:
            shutil.rmtree(core.config['gratia.gridftp-temp-dir'])
            shutil.rmtree(core.config['gratia.config.dir'] + "/gridftp-transfer")
        
    #=========================================
    # This test cleans up glexec related files
    #=========================================
    def test_05_cleanup_glexec(self):
        core.skip_ok_unless_installed('gratia-probe-glexec')
        files.remove("/var/lib/gratia/tmp/GlexecAccountingProbeState")
        files.remove("/var/log/glexec.log")
        files.remove("/var/lib/gratia/data/glexec_plugin.chk")

        #files.remove doesn't remove non-empty directories. In such a case, use shutil.rmtree command
        try:
            files.remove(core.config['gratia.glexec-temp-dir'])
            files.remove(core.config['gratia.config.dir'] + "/glexec")
        except:
            shutil.rmtree(core.config['gratia.glexec-temp-dir'])
            shutil.rmtree(core.config['gratia.config.dir'] + "/glexec")
        
    #=========================================
    # This test cleans up dcache related files 
    #=========================================
    def test_06_cleanup_dcache(self):
        core.skip_ok_unless_installed('gratia-probe-dcache-storage')
        files.remove("/var/lib/gratia/tmp/dCache-storage_meter.cron.pid")
        #files.remove doesn't remove non-empty directories. In such a case, use shutil.rmtree command
        try:
            files.remove(core.config['gratia.dcache-temp-dir'])
            files.remove(core.config['gratia.config.dir'] + "/dCache-storage")
        except:
            shutil.rmtree(core.config['gratia.dcache-temp-dir'])
            shutil.rmtree(core.config['gratia.config.dir'] + "/dCache-storage")

    #=========================================
    # This test cleans up condor related files
    #=========================================
    def test_07_cleanup_condor(self):
        core.skip_ok_unless_installed('gratia-probe-condor')
        files.remove("/var/lib/gratia/data/gratia_certinfo_condor*")
        files.remove("/var/lib/gratia/data/history.1211*")
        #files.remove doesn't remove non-empty directories. In such a case, use shutil.rmtree command
        try:
            files.remove(core.config['gratia.condor-temp-dir'])
            files.remove(core.config['gratia.config.dir'] + "/condor")
        except:
            shutil.rmtree(core.config['gratia.condor-temp-dir'])
            shutil.rmtree(core.config['gratia.config.dir'] + "/condor")
        
    #===============================
    # This test stops psacct service
    #===============================
    def test_08_stop_psacct_service(self):
        core.skip_ok_unless_installed('gratia-probe-psacct')        
        command = ('service', 'psacct', 'stop')
        stdout, _, fail = core.check_system(command, 'Stop psacct')
        self.assert_(stdout.find('FAILED') == -1, fail)

    #=========================================
    # This test cleans up psacct related files
    #=========================================
    def test_09_cleanup_psacct(self):
        core.skip_ok_unless_installed('gratia-probe-psacct')
        files.remove("/var/lib/gratia/account/pacct")
        files.remove("/var/lib/gratia/account/pacct.creation")
        files.remove("/var/lib/gratia/backup/*")
        #files.remove doesn't remove non-empty directories. In such a case, use shutil.rmtree command
        try:
            files.remove(core.config['gratia.psacct-temp-dir'])
            files.remove(core.config['gratia.config.dir'] + "/psacct")
        except:
            shutil.rmtree(core.config['gratia.psacct-temp-dir'])
            shutil.rmtree(core.config['gratia.config.dir'] + "/psacct")

    #=======================================
    # This test cleans up bdii related files
    #=======================================
    def test_10_cleanup_bdii(self):
        core.skip_ok_unless_installed('gratia-probe-bdii-status')
        command = ('rm', '-rf', core.config['gratia.bdii-temp-dir'])
        #files.remove doesn't remove non-empty directories. In such a case, use shutil.rmtree command
        try:
            files.remove(core.config['gratia.bdii-temp-dir'])
            files.remove(core.config['gratia.config.dir'] + "/bdii-status")
        except:
            shutil.rmtree(core.config['gratia.bdii-temp-dir'])
            shutil.rmtree(core.config['gratia.config.dir'] + "/bdii-status")
        
        
    #======================================
    # This test cleans up pbs related files
    #======================================
    def test_11_cleanup_pbs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf')
        files.remove("/var/lib/gratia/tmp/urCollectorBuffer.pbs")
        try:
            files.remove(core.config['gratia.pbs-temp-dir'])
            files.remove(core.config['gratia.config.dir'] + "/pbs-lsf")
            files.remove("/var/lib/gratia/pbs-lsf")
            files.remove("/var/spool/pbs/server_priv/accounting")
            files.remove("/var/lib/gratia/tmp/urCollector")
        except:
            shutil.rmtree(core.config['gratia.pbs-temp-dir'])
            shutil.rmtree(core.config['gratia.config.dir'] + "/pbs-lsf")
            shutil.rmtree("/var/lib/gratia/pbs-lsf")
            shutil.rmtree("/var/spool/pbs/server_priv/accounting")
            shutil.rmtree("/var/lib/gratia/tmp/urCollector")