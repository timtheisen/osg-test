import os
import re
import shutil
import unittest
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.certificates as certs
import osgtest.library.osgunittest as osgunittest

class TestCert(osgunittest.OSGTestCase):

    def test_01_install_ca_and_crl(self):
        certs_dir= '/etc/grid-security/certificates'
        core.state['certs.dir_created'] = False        
        certs.configure_openssl()

        if not os.path.exists(certs_dir):
            os.makedirs(certs_dir, 0755)
            self.assert_(os.path.exists(certs_dir), "could not create /etc/grid-security/certificates")
            core.state['certs.dir_created'] = True

        # Generate CA, key and CRL
        certs.create_ca(certs_dir)
        certs.create_crl()

        # Grab hashes from CA
        command = ('openssl', 'x509', '-in', core.config['certs.test-ca'], '-noout', '-subject_hash')
        core.config['certs.test-ca-hash'] = core.check_system(command, "Couldn't get old hash of test cert")[0].strip()
        hashes = [core.config['certs.test-ca-hash']]

        # openssl-1.x has a -subject_hash_old flag that doesn't exist in openssl-0.x
        openssl_version = core.get_package_envra("openssl")[2]
        if re.match('1.+', openssl_version):
            command = ('openssl', 'x509', '-in', core.config['certs.test-ca'], '-noout', '-subject_hash_old')
            core.config['certs.test-ca-hash-old'] = core.check_system(command, "Couldn't get old hash of test cert")[0].strip()
            hashes.append(core.config['certs.test-ca-hash-old'])

        # Add signing policy and namespaces files
        shutil.copy('/usr/share/osg-test/OSG-Test-CA.namespaces', '/etc/grid-security/certificates')
        shutil.copy('/usr/share/osg-test/OSG-Test-CA.signing_policy', '/etc/grid-security/certificates')
        files.replace('/etc/grid-security/certificates/OSG-Test-CA.namespaces',
                      "# @(#)xyxyxyxy.namespaces",
                      "# @(#)%s.namespaces" % core.config['certs.test-ca-hash'],
                      backup=False)
        files.replace('/etc/grid-security/certificates/OSG-Test-CA.namespaces',
                      "#    hash     : xyxyxyxy",
                      "#    hash     : %s" % core.config['certs.test-ca-hash'],
                      backup=False)

        # Create hash links
        basename = 'OSG-Test-CA'
        links = [('.pem', '.0'),
                 ('.signing_policy', '.signing_policy'),
                 ('.namespaces', '.namespaces'),
                 ('.r0', '.r0')]
        for subject_hash in hashes:
            for source, link in links:
                source = basename + source
                link = '/etc/grid-security/certificates/' + subject_hash + link
                os.symlink(source, link)
        
    def test_02_install_host_cert(self):
        host_cert_dir = '/etc/grid-security'
        host_cert = host_cert_dir + "/hostcert.pem"
        host_key = host_cert_dir + "/hostkey.pem"
        core.config['certs.hostcert'] = host_cert
        core.config['certs.hostkey'] = host_key
        core.state['certs.hostcert_created'] = False
        
        if core.options.hostcert:
            self.assertFalse(os.path.exists(host_cert) or os.path.exists(host_key), "hostcert or hostkey already exist")
            certs.create_host_cert(host_cert_dir)
            core.state['certs.hostcert_created'] = True

