import os
import shutil

import osgtest.library.core as core
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

    #===========================================================================
    # This test removes the http certificates
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
       
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        #open the above file and write admin password information on the go
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        
        #Command to drop the gratia database is:
        #echo "drop database gratia;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" -B --unbuffered  --user=root --port=3306         
        command = "echo \"drop database gratia;\" | mysql --defaults-extra-file=\"" + filename + "\" -B --unbuffered  --user=root --port=3306"
        core.check_system(command, 'Unable to drop Gratia Database !', shell=True)
        os.remove(filename)
        
    #===========================================================================
    # This test cleans up the appropriate gratia directory
    #===========================================================================
    def test_03_cleanup_etcgratia_directory(self):
        core.skip_ok_unless_installed('gratia-service')
        directory = '/etc/gratia/' + core.config['gratia.directory']
        command = ('rm', '-rf', directory)
        core.check_system(command, 'Unable to clean up gratia directory!')
        
    #===========================================================================
    # This test cleans up files in core.config['gratia.gridftp-temp-dir']
    #===========================================================================
    def test_04_cleanup_temp_gratiafiles(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        command = ('rm', '-rf', core.config['gratia.gridftp-temp-dir'])
        core.check_system(command, 'Unable to clean up core.config[\'gratia.gridftp-temp-dir\'] !')
    
    #===========================================================================
    # This test removes /var/lib/gratia/tmp/GridftpAccountingProbeState
    #===========================================================================
    def test_05_cleanup_temp_gridftpaccountingprobestate(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        command = ('rm', '-rf', '/var/lib/gratia/tmp/GridftpAccountingProbeState')
        core.check_system(command, 'Unable to clean up /var/lib/gratia/tmp/GridftpAccountingProbeState !')

    #===========================================================================
    # This test removes /var/log/gridftp.log
    #===========================================================================
    def test_06_cleanup_varlog_gridftplog(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        command = ('rm', '-rf', '/var/log/gridftp.log')
        core.check_system(command, 'Unable to clean up  /var/log/gridftp.log!')
    
    #===========================================================================
    # This test removes /var/log/gridftp-auth.log
    #===========================================================================
    def test_07_cleanup_varlog_gridftpauthlog(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        command = ('rm', '-rf', '/var/log/gridftp-auth.log')
        core.check_system(command, 'Unable to clean up  /var/log/gridftp-auth.log!')
        
   
    #===========================================================================
    # This test cleans up /etc/gratia/gridftp-transfer
    #===========================================================================
    def test_08_cleanup_etcgratia_gridftp_transfer(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-gridftp-transfer')
        command = ('rm', '-rf', '/etc/gratia/gridftp-transfer')
        core.check_system(command, 'Unable to clean up  /etc/gratia/gridftp-transfer!')
        
    #===========================================================================
    # This test cleans up files in core.config['gratia.glexec-temp-dir']
    #===========================================================================
    def test_09_cleanup_temp_glexec(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-glexec')
        command = ('rm', '-rf', core.config['gratia.glexec-temp-dir'])
        core.check_system(command, 'Unable to clean up core.config[\'gratia.glexec-temp-dir\'] !')

    #===========================================================================
    # This test removes /var/lib/gratia/tmp/GlexecAccountingProbeState
    #===========================================================================
    def test_10_cleanup_temp_glexecprobestate(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-glexec')
        command = ('rm', '-rf', '/var/lib/gratia/tmp/GlexecAccountingProbeState')
        core.check_system(command, 'Unable to clean up /var/lib/gratia/tmp/GlexecAccountingProbeState !')
        
    #===========================================================================
    # This test removes /var/log/glexec.log
    #===========================================================================
    def test_11_cleanup_varlog_glexeclog(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-glexec')
        command = ('rm', '-rf', '/var/log/glexec.log')
        core.check_system(command, 'Unable to clean up  /var/log/glexec.log!')
        
    
    #===========================================================================
    # This test cleans up /var/lib/gratia/data/glexec_plugin.chk
    #===========================================================================
    def test_12_cleanup_etcgratia_glexec(self):
        core.skip_ok_unless_installed('gratia-service', 'gratia-probe-glexec')
        command = ('rm', '-rf', '/var/lib/gratia/data/glexec_plugin.chk')
        core.check_system(command, 'Unable to clean up /var/lib/gratia/data/glexec_plugin.chk!')
