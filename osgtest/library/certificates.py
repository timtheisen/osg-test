"""Utilities for creating CAs, certificates and CRLs"""

import os
import re
import pwd
import shutil

import osgtest.library.core as core
import osgtest.library.files as files

OPENSSL_CONFIG = '/etc/pki/tls/openssl.cnf'
OPENSSL_DIR = '/etc/pki/CA/'
CERT_EXT_CONFIG = '/usr/share/osg-test/openssl-cert-extensions.conf'
HOST_REQUEST = "host_req"
DAYS = '10'
SN = "A1B2C3D4E5F6"

def create_ca(ca_path):
    """Create a CA similar to DigiCert's """
    ca_key = os.path.splitext(ca_path)[0] + '.key'
    ca_subject = '/DC=org/DC=Open Science Grid/O=OSG Test/CN=OSG Test CA'

    command = ('openssl', 'genrsa', '-out', ca_key, '2048')
    core.check_system(command, 'generate CA private key')

    command = ('openssl', 'req', '-sha256', '-new', '-x509', '-out', ca_path, '-key',
               ca_key, '-subj', ca_subject, '-config', OPENSSL_CONFIG, '-days', DAYS)
    core.check_system(command, 'generate CA')

def create_host_cert(cert_path, key_path, ca_path):
    """Create a hostcert similar to DigiCert's"""
    ca_key = os.path.splitext(ca_path)[0] + '.key'
    host_pk_der = "hostkey.der"
    host_cert_subject = '/DC=org/DC=Open Science Grid/O=OSG Test/OU=Services/CN=' + core.get_hostname()

    command = ('openssl', 'req', '-new', '-nodes', '-out', HOST_REQUEST, '-keyout', host_pk_der, '-subj',
               host_cert_subject)
    core.check_system(command, 'generate host cert request')
    # Have to run the private key through RSA to get proper format (-keyform doesn't work in openssl > 0.9.8)
    command = ('openssl', 'rsa', '-in', host_pk_der, '-outform', 'PEM', '-out', key_path)
    core.check_system(command, 'generate host private key')
    files.remove(host_pk_der)
    os.chmod(core.config['certs.hostkey'], 0400)

    command = ('openssl', 'ca', '-md', 'sha256', '-config', OPENSSL_CONFIG, '-cert', ca_path, '-keyfile',
               ca_key, '-days', DAYS, '-policy', 'policy_anything', '-preserveDN', '-extfile',
               CERT_EXT_CONFIG, '-in', HOST_REQUEST, '-notext', '-out', cert_path, '-outdir', '.',
               '-batch')
    core.check_system(command, 'generate host cert')

def create_user_cert(cert_path, username, ca_path):
    """Create a usercert similar to DigiCert's"""
    keypath = cert_path.replace('cert.pem', 'key.pem')
    ca_key = os.path.splitext(ca_path)[0] + '.key'
    user_request = 'user_req'
    user_cert_subject = '/DC=org/DC=Open Science Grid/O=OSG Test/OU=People/CN=' + username

    command = ("openssl", "req", "-sha256", "-new", "-out", user_request, "-keyout", keypath, "-subj",
               user_cert_subject, '-passout', 'pass:' + core.options.password)
    core.check_system(command, 'generate user cert request and key')
    os.chmod(keypath, 0400)

    command = ('openssl', 'ca', '-md', 'sha256', '-config', OPENSSL_CONFIG, '-cert', ca_path, '-keyfile', ca_key,
               '-days', DAYS, '-policy', 'policy_anything', '-preserveDN', '-extfile', CERT_EXT_CONFIG, '-in',
               user_request, '-notext', '-out', cert_path, '-outdir', '.', '-batch')
    core.check_system(command, "generate user cert")

def create_crl(ca_path):
    """Create CRL to accompany our CA."""
    crl_path = os.path.splitext(ca_path)[0] + '.r0'
    ca_key = os.path.splitext(ca_path)[0] + '.key'
    command = ("openssl", "ca", "-gencrl", "-config", OPENSSL_CONFIG, "-cert", ca_path, "-keyfile",
               ca_key, "-crldays", DAYS, "-out", crl_path)
    core.check_system(command, "generate CRL")

def cleanup_files():
    """Cleanup openssl files and config we laid down"""


def certificate_info(path):
    """Extracts and returns the subject and issuer from an X.509 certificate."""
    command = ('openssl', 'x509', '-noout', '-subject', '-issuer', '-in', path)
    status, stdout, stderr = core.system(command)
    if (status != 0) or (stdout is None) or (stderr is not None):
        raise OSError(status, stderr)
    if len(stdout.strip()) == 0:
        raise OSError(status, stdout)
    subject_issuer_re = r'subject\s*=\s*([^\n]+)\nissuer\s*=\s*([^\n]+)\n'
    matches = re.match(subject_issuer_re, stdout).groups()
    if matches is None:
        raise OSError(status, stdout)
    subject, issuer = matches
    return (subject, issuer)

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
