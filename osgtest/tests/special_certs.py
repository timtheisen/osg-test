import os
import re
import shutil
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.certificates as certs
import osgtest.library.osgunittest as osgunittest

class TestCert(osgunittest.OSGTestCase):

    def test_01_install_ca_and_crl(self):
        certs_dir = '/etc/grid-security/certificates'
        core.state['certs.dir_created'] = False
        core.state['certs.ca_created'] = False
        ca_basename = 'OSG-Test-CA'

        # Generate CA, key and CRL. If the CA already exists, we can skip everything
        core.config['certs.test-ca'] = os.path.join(certs_dir, ca_basename + '.pem')
        if os.path.exists(core.config['certs.test-ca']):
            self.skip_ok('OSG TEST CA already exists')

        # Lay down openssl config
        files.replace(certs.OPENSSL_CONFIG, "# crl_extensions	= crl_ext",
                      "crl_extensions	= crl_ext",
                      owner="CA")
        files.replace(certs.OPENSSL_CONFIG,
                      "basicConstraints = CA:true",
                      "basicConstraints = critical, CA:true",
                      backup=False)
        files.replace(certs.OPENSSL_CONFIG,
                      "# keyUsage = cRLSign, keyCertSign",
                      "keyUsage = critical, digitalSignature, cRLSign, keyCertSign",
                      backup=False)
        files.replace(certs.OPENSSL_CONFIG,
                      "dir		= ../../CA		# Where everything is kept",
                      "dir		= %s		# Where everything is kept" % certs.OPENSSL_DIR,
                      backup=False)
        files.replace(certs.CERT_EXT_CONFIG,
                      'subjectAltName=DNS:##HOSTNAME##',
                      'subjectAltName=DNS:%s' % core.get_hostname(),
                      owner="CA")
        files.write(certs.OPENSSL_DIR + "index.txt", "", backup=False)
        files.write(certs.OPENSSL_DIR + "serial", certs.SN, backup=False)
        files.write(certs.OPENSSL_DIR + "crlnumber", "01", backup=False)

        if not os.path.exists(certs_dir):
            os.makedirs(certs_dir, 0755)
            core.state['certs.dir_created'] = True

        certs.create_ca(core.config['certs.test-ca'])
        certs.create_crl(core.config['certs.test-ca'])

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
        tests_dir = '/usr/share/osg-test'
        namespace_file = os.path.join(certs_dir, ca_basename + '.namespaces')
        shutil.copy(os.path.join(tests_dir, ca_basename + '.namespaces'), certs_dir)
        shutil.copy(os.path.join(tests_dir, ca_basename + '.signing_policy'), certs_dir)
        files.replace(namespace_file,
                      "# @(#)xyxyxyxy.namespaces",
                      "# @(#)%s.namespaces" % core.config['certs.test-ca-hash'],
                      backup=False)
        files.replace(namespace_file,
                      "#    hash     : xyxyxyxy",
                      "#    hash     : %s" % core.config['certs.test-ca-hash'],
                      backup=False)

        # Create hash links
        links = [('.pem', '.0'),
                 ('.signing_policy', '.signing_policy'),
                 ('.namespaces', '.namespaces'),
                 ('.r0', '.r0')]
        for subject_hash in hashes:
            for source_ext, link_ext in links:
                source = ca_basename + source_ext
                link = os.path.join(certs_dir, subject_hash + link_ext)
                os.symlink(source, link)
        core.state['certs.ca_created'] = True

    def test_02_install_host_cert(self):
        core.state['certs.hostcert_created'] = False
        core.config['certs.hostcert'] = '/etc/grid-security/hostcert.pem'
        core.config['certs.hostkey'] = core.config['certs.hostcert'].replace('cert.pem', 'key.pem')
        if core.options.hostcert:
            self.assertFalse(os.path.exists(core.config['certs.hostcert']) or
                             os.path.exists(core.config['certs.hostkey']),
                             "hostcert or hostkey already exist")
            certs.create_host_cert(core.config['certs.hostcert'],
                                   core.config['certs.hostkey'],
                                   core.config['certs.test-ca'])
            core.state['certs.hostcert_created'] = True

