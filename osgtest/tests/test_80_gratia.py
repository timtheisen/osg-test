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

    # ==========================================================================

#Need to determine if gratia needs to be explicitly stopped...
#===============================================================================
#     def test_01_stop_gratia(self):
#         core.skip_ok_unless_installed('gratia-service')
#         self.skip_ok_unless(core.state['voms.started-server'], 'did not start server')
# 
#         command = ('service', 'voms', 'stop')
#         stdout, stderr, fail = core.check_system(command, 'Stop VOMS server')
#         self.assertEqual(stdout.find('FAILED'), -1, fail)
#         self.assert_(not os.path.exists(core.config['voms.lock-file']),
#                      'VOMS server lock file still exists')
#===============================================================================


    def test_01_remove_certs(self):
        # Do the keys first, so that the directories will be empty for the certs.
        self.remove_cert('certs.httpkey')
        self.remove_cert('certs.httpcert')

    def test_02_uninstall_gratia_database(self):
        core.skip_ok_unless_installed('gratia-service')    
       
        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        #print filename
        f = open(filename,'w')
        f.write("[client]\n")
        f.write("password=admin\n")
        f.close()
        
        #Command to drop the gratia database is:
        #echo "drop database gratia;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" -B --unbuffered  --user=root --port=3306         
        command = "echo \"drop database gratia;\" | mysql --defaults-extra-file=\"" + filename + "\" -B --unbuffered  --user=root --port=3306"
        status, stdout, stderr = core.system(command, shell=True)
        self.assertEqual(status, 0, 'Unable to install Gratia Database !')
        os.remove(filename)
        