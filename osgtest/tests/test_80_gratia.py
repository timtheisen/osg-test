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
