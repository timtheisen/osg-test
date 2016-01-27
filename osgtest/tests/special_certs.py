import os
import osgtest.library.core as core
from cagen import CA
import osgtest.library.osgunittest as osgunittest

class TestCert(osgunittest.OSGTestCase):

    def test_01_install_ca(self):
        core.state['certs.ca_created'] = False
        core.config['certs.test-ca'] = '/etc/grid-security/certificates/OSG-Test-CA.pem'
        self.skip_ok_if(os.path.exists(core.config['certs.test-ca']), 'OSG TEST CA already exists')
        CA('/DC=org/DC=Open Science Grid/O=OSG Test/CN=OSG Test CA')
        core.state['certs.ca_created'] = True

    def test_02_install_host_cert(self):
        self.skip_ok_unless(os.path.exists(core.config['certs.test-ca']), "OSG Test CA doesn't exist")
        core.state['certs.hostcert_created'] = False
        grid_dir = '/etc/grid-security/'
        core.config['certs.hostcert'] = os.path.join(grid_dir, 'hostcert.pem')
        core.config['certs.hostkey'] = os.path.join(grid_dir, 'hostkey.pem')

        if core.options.hostcert and not os.path.exists(core.config['certs.hostcert']):
            test_ca = CA.load(core.config['certs.test-ca'])
            test_ca.hostcert()
            core.state['certs.hostcert_created'] = True

