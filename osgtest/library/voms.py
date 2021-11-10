import pwd
import os
import shutil
import tempfile

import cagen
from osgtest.library import core
from osgtest.library import files
from osgtest.library import mysql
from osgtest.library import osgunittest


VONAME = "osgtestvo"


def _get_sqlloc():
    # Find full path to libvomsmysql.so
    command = ('rpm', '--query', '--list', 'voms-mysql-plugin')
    stdout = core.check_system(command, 'List VOMS-MySQL files')[0]
    voms_mysql_files = stdout.strip().split('\n')
    voms_mysql_so_path = None
    for voms_mysql_path in voms_mysql_files:
        if 'libvomsmysql.so' in voms_mysql_path:
            voms_mysql_so_path = voms_mysql_path
    assert voms_mysql_so_path is not None, \
                'Could not find VOMS MySQL shared library path'
    assert os.path.exists(voms_mysql_so_path), \
                'VOMS MySQL shared library path does not exist'

    return voms_mysql_so_path


def create_vo(vo, dbusername='voms_osgtest', dbpassword='secret', vomscert='/etc/grid-security/voms/vomscert.pem', vomskey='/etc/grid-security/voms/vomskey.pem'):
    """Create the given VO using the voms_install_db script that comes with voms-server. A new
    database user with the given username/password is created with access to the VO database.
    """
    mysql.execute("CREATE USER '%(dbusername)s'@'localhost';" % locals())

    command = ['/usr/share/voms/voms_install_db',
               '--voms-vo=' + vo,
               '--port=15151',
               '--db-type=mysql',
               '--db-admin=root',
               '--voms-name=' + dbusername,
               '--voms-pwd=' + dbpassword,
               '--sqlloc=' + _get_sqlloc(),
               '--vomscert=' + vomscert,
               '--vomskey=' + vomskey,
               ]

    core.check_system(command, 'Create VO')


def advertise_lsc(vo, hostcert='/etc/grid-security/hostcert.pem'):
    """Create the VO directory and .lsc file under /etc/grid-security/vomsdir for the given VO"""
    host_dn, host_issuer = cagen.certificate_info(hostcert)
    hostname = core.get_hostname()
    lsc_dir = os.path.join('/etc/grid-security/vomsdir', vo)
    if not os.path.isdir(lsc_dir):
        os.makedirs(lsc_dir)
    vo_lsc_path = os.path.join(lsc_dir, hostname + '.lsc')
    files.write(vo_lsc_path, (host_dn + '\n', host_issuer + '\n'), backup=False, chmod=0o644)


def advertise_vomses(vo, hostcert='/etc/grid-security/hostcert.pem'):
    """Edit /etc/vomses to advertise the current host as the VOMS server for the given VO.
    Caller is responsible for preserving and restoring /etc/vomses.
    """
    host_dn, _ = cagen.certificate_info(hostcert)
    hostname = core.get_hostname()
    vomses_path = '/etc/vomses'
    contents = ('"%s" "%s" "%d" "%s" "%s"\n' %
                (vo, hostname, 15151, host_dn, vo))
    files.write(vomses_path, contents, backup=False, chmod=0o644)


def add_user(vo, usercert):
    """Add the user identified by the given cert to the specified VO. Uses direct MySQL statements instead of voms-admin.
    The CA cert that issued the user cert must already be in the database's 'ca' table - this happens automatically if
    the CA cert is in /etc/grid-security/certificates when the VOMS database is created.
    """
    usercert_dn, usercert_issuer = cagen.certificate_info(usercert)
    dbname = 'voms_' + vo

    # Find the index in the "ca" table ("cid") for the OSG Test CA that gets created by voms_install_db.
    output, _, _, = mysql.check_execute(r'''SELECT cid FROM ca WHERE ca='%(usercert_issuer)s';''' % locals(),
                                        'Get ID of user cert issuer from database', dbname)
    output = output.strip()
    assert output, "User cert issuer not found in database"
    ca = int(output)

    mysql.check_execute(r'''
        INSERT INTO `usr` VALUES (1,'%(usercert_dn)s',%(ca)d,NULL,'root@localhost',NULL);
        INSERT INTO `m` VALUES (1,1,1,NULL,NULL);''' % locals(),
        'Add VO user', dbname)


def destroy_lsc(vo):
    """Remove the VO directory and .lsc file from under /etc/grid-security/vomsdir"""
    lsc_dir = os.path.join('/etc/grid-security/vomsdir', vo)
    if os.path.exists(lsc_dir):
        shutil.rmtree(lsc_dir)


def destroy_db(vo, dbusername=None):
    """Destroy the VOMS database for the VO. If given, also remove the VO user from the database"""
    dbname = 'voms_' + vo

    mysql.execute('DROP DATABASE IF EXISTS `%s`;' % dbname)
    if dbusername:
        mysql.execute("DROP USER '%s'@'localhost';" % dbusername)


def destroy_voms_conf(vo):
    """Remove the VOMS config for the VO"""
    vodir = os.path.join('/etc/voms', vo)
    shutil.rmtree(vodir, ignore_errors=True)


def proxy_direct(username=None, password=None,
                 cert_path=None, key_path=None,
                 fqan=f'/{VONAME}/Role=NULL/Capability=NULL'):
    f"""Generate a user proxy and directly sign VOMS attributes using the test VOMS cert and key
    - username: owner of the generated proxy file (default osg-test username)
    - password: proxy password (default: osg-test password)
    - cert_path: path to the user certificate (default: ~username/.globus/usercert.pem)
    - key_path: path to the user key (default: ~username/.globus/userkey.pem)
    - fqan: VOMS attribute (default: /{VONAME}/Role=NULL/Capability=NULL)
    """
    if username:
        user = pwd.getpwnam(username)
        uid = user.pw_uid
        gid = user.pw_gid
    else:
        username = core.options.username
        uid = core.state['user.uid']
        gid = core.state['user.gid']

    if not password:
        password = core.options.password
    if not password.endswith('\n'):
        password = password + '\n'
    if not cert_path:
        cert_path = os.path.join(os.path.expanduser(f'~{username}'), '.globus/usercert.pem')
    if not key_path:
        key_path = os.path.join(os.path.expanduser(f'~{username}'), '.globus/userkey.pem')

    # voms-proxy-direct requires that the user cert/key are owned by the user running the command
    filemap = dict()
    for src in (cert_path, key_path):
        dest = tempfile.NamedTemporaryFile()
        filemap[src] = dest
        shutil.copy2(src, dest.name)

    proxy_path = f'/tmp/x509up_u{core.state["user.uid"]}'
    command = ('voms-proxy-direct',
               '-rfc',
               '-debug',
               '-bits', '2048',
               '-voms', VONAME,
               '-uri', core.get_hostname(),
               '-fqan', fqan,
               '-cert', filemap[cert_path].name,
               '-key', filemap[key_path].name,
               '-hostcert', core.config['certs.hostcert'],
               '-hostkey', core.config['certs.hostkey'],
               '-out', proxy_path)
    core.check_system(command, 'Run voms-proxy-direct', stdin=password)
    os.chown(proxy_path, uid, gid)

def is_installed():
    """Return True if the dependencies for setting up and using VOMS are installed.
    EL7 requires a minimum version of the voms-server package to get the service file fix from SOFTWARE-2357.
    """
    for dep in 'voms-server', 'voms-clients', 'voms-mysql-plugin', mysql.client_rpm(), mysql.server_rpm():
        if not core.dependency_is_installed(dep):
            return False

    return True


def skip_ok_unless_installed():
    """OkSkip if the dependencies for setting up and using VOMS are not installed."""
    if not is_installed():
        raise osgunittest.OkSkipException('VOMS server requirements not installed')
