"""Utilities for creating CAs, certificates and CRLs"""

import os
import re
import pwd
import shutil

import osgtest.library.core as core
import osgtest.library.files as files

openssl_config = '/etc/pki/tls/openssl.cnf'
openssl_dir = '/etc/pki/CA/'
cert_ext_config = '/usr/share/osg-test/openssl-cert-extensions.conf' 
host_request = "host_req"
ca_subject = '/DC=org/DC=Open Science Grid/O=OSG Test/CN=OSG Test CA'
days = '10'
sn = "A1B2C3D4E5F6"

def configure_openssl():
    """Lays down files and configuration for creating CAs, certs and CRLs"""
    # Instead of patching openssl's config file
    files.replace(openssl_config, "# crl_extensions	= crl_ext", "crl_extensions	= crl_ext", owner="CA")
    files.replace(openssl_config, "basicConstraints = CA:true", "basicConstraints = critical, CA:true", backup=False)
    files.replace(openssl_config,
                  "# keyUsage = cRLSign, keyCertSign",
                  "keyUsage = critical, digitalSignature, cRLSign, keyCertSign",
                  backup=False)
    files.replace(openssl_config,
                  "dir		= ../../CA		# Where everything is kept",
                  "dir		= %s		# Where everything is kept" % openssl_dir,
                  backup=False)

    # Patches openssl-cert-extensions.conf
    files.replace(cert_ext_config,
                  'subjectAltName=DNS:##HOSTNAME##',
                  'subjectAltName=DNS:%s' % core.get_hostname(),
                  owner="CA")
    
    # Put down necessary files
    files.write(openssl_dir + "index.txt", "", backup=False)
    files.write(openssl_dir + "serial", sn, backup=False)
    files.write(openssl_dir + "crlnumber", "01", backup=False)

def create_ca(path):
    """Create a CA similar to DigiCert's """
    core.config['certs.test-ca'] = path + "/OSG-Test-CA.pem"
    core.config['certs.test-ca-key'] = path + "/OSG-Test-CA.key"

    command = ("openssl", "genrsa", "-out", core.config['certs.test-ca-key'], "2048")
    core.check_system(command, 'generate CA private key')

    command = ("openssl", "req", "-new", "-x509", "-out", core.config['certs.test-ca'], "-key", 
               core.config['certs.test-ca-key'], "-subj", ca_subject, "-config", openssl_config, "-days", days)
    core.check_system(command, 'generate CA')

def create_host_cert(path):
    """Create a cert similar to DigiCert's"""
    host_pk_der = "hostkey.der"
    host_cert_subject = '/DC=org/DC=Open Science Grid/O=OSG Test/OU=Services/CN=' + core.get_hostname()
    core.config['certs.hostkey'] = path + "/hostkey.pem"
    core.config['certs.hostcert'] = path + "/hostcert.pem"

    command = ("openssl", "req", "-new", "-nodes", "-out", host_request, "-keyout", host_pk_der,"-subj", host_cert_subject)
    core.check_system(command, 'generate host cert request')
    # Have to run the private key through RSA to get proper format (-keyform doesn't work in openssl > 0.9.8)
    command = ("openssl", "rsa", "-in", host_pk_der, "-outform", "PEM", "-out", core.config['certs.hostkey']) 
    core.check_system(command, "generate host private key") 
    files.remove(host_pk_der)
    os.chmod(core.config['certs.hostkey'], 0400)

    command = ("openssl", "ca", "-config", openssl_config, "-cert", core.config['certs.test-ca'], "-keyfile",
               core.config['certs.test-ca-key'], "-days", days, "-policy", "policy_anything", "-preserveDN", "-extfile",
               cert_ext_config, "-in", host_request, "-notext","-out", core.config['certs.hostcert'], "-outdir", ".",
               "-batch")
    core.check_system(command, "generate host cert")

 
def create_crl():
    """Create CRL to accompany our CA."""
    core.config['certs.test-crl'] = os.path.dirname(core.config['certs.test-ca']) + "/OSG-Test-CA.r0"
        
    command = ("openssl", "ca", "-gencrl", "-config", openssl_config, "-cert", core.config['certs.test-ca'], "-keyfile",
               core.config['certs.test-ca-key'], "-crldays", days, "-out", core.config['certs.test-crl'])
    core.check_system(command, "generate CRL")

def cleanup_files():
    """Cleanup openssl files and config we laid down"""
    # Cleanup files from previous runs
    files.remove(openssl_dir + "index.txt*")
    files.remove(openssl_dir + "crlnumber*")
    files.remove(openssl_dir + "serial*")
    files.remove(openssl_dir + "%s.pem" % sn)
    files.remove(host_request)
    
    files.restore(openssl_config, "CA")
    files.restore(cert_ext_config, "CA")

def certificate_info(path):
    """Extracts and returns the subject and issuer from an X.509 certificate."""
    command = ('openssl', 'x509', '-noout', '-subject', '-issuer', '-in', path)
    status, stdout, stderr = core.system(command)
    if (status != 0) or (stdout is None) or (stderr is not None):
        raise OSError(status, stderr)
    if len(stdout.strip()) == 0:
        raise OSError(status, stdout)
    subject_issuer_re = r'subject\s*=\s*([^\n]+)\nissuer\s*=\s*([^\n]+)\n'
    matches = re.match(subject_issuer_re, stdout)
    if matches is None:
        raise OSError(status, stdout)
    return (matches.group(1), matches.group(2))

def install_cert(target_key, source_key, owner_name, permissions):
    """
    Carefully install a certificate with the given key from the given
    source path, then set ownership and permissions as given.  Record
    each directory and file created by this process into the config
    dictionary; do so immediately after creation, so that the
    remove_cert() function knows exactly what to remove/restore.
    """
    target_path = core.config[target_key]
    target_dir = os.path.dirname(target_path)
    source_path = core.config[source_key]
    user = pwd.getpwnam(owner_name)

    # Using os.path.lexists because os.path.exists return False for broken symlinks
    if os.path.lexists(target_path):
        backup_path = target_path + '.osgtest.backup'
        shutil.move(target_path, backup_path)
        core.state[target_key + '-backup'] = backup_path

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        core.state[target_key + '-dir'] = target_dir
        os.chown(target_dir, user.pw_uid, user.pw_gid)
        os.chmod(target_dir, 0755)

    shutil.copy(source_path, target_path)
    core.state[target_key] = target_path
    os.chown(target_path, user.pw_uid, user.pw_gid)
    os.chmod(target_path, permissions)

def remove_cert(target_key):
    """
    Carefully removes a certificate with the given key.  Removes all
    paths associated with the key, as created by the install_cert()
    function.
    """
    if core.state.has_key(target_key):
        os.remove(core.state[target_key])
    if core.state.has_key(target_key + '-backup'):
        shutil.move(core.state[target_key + '-backup'],
                    core.state[target_key])
    if core.state.has_key(target_key + '-dir'):
        target_dir = core.state[target_key + '-dir']
        if len(os.listdir(target_dir)) == 0:
            os.rmdir(target_dir)
