import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest

class TestGratia(osgunittest.OSGTestCase):

    def test_01_gratia_admin_webpage (self):
         
        core.skip_ok_unless_installed('gratia-service')
        command = ('curl', 'http://fermicloud316.fnal.gov:8880/gratia-administration/status.html?wantDetails=0')
        status, stdout, stderr = core.system(command)
        print "stdout is: " + str(stdout)
        print "stderr is: " + str(stderr)
        self.assertEqual(status, 0, 'Unable to launch gratia admin webpage')