import pwd
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest


XROOTD_CFG_TEXT = """\
cms.space min 2g 5g
xrootd.seclib libXrdSec.so
sec.protocol /usr/lib64 gsi -certdir:/etc/grid-security/certificates \
    -cert:/etc/grid-security/xrd/xrdcert.pem \
    -key:/etc/grid-security/xrd/xrdkey.pem \
    -crl:3 \
    --gmapopt:10 \
    --gmapto:0 \
    %s
acc.authdb /etc/xrootd/auth_file
ofs.authorize
xrd.tls /etc/grid-security/xrd/xrdcert.pem /etc/grid-security/xrd/xrdkey.pem
xrd.tlsca noverify
"""

# XRootD configuration necessaryfor osg-xrootd-standalone
META_XROOTD_CFG_TEXT = """\
set rootdir = /
set resourcename = OSG_TEST_XROOTD_STANDALONE
"""

AUTHFILE_TEXT = """\
u * /tmp a /usr/share/ r
u = /tmp/@=/ a
u xrootd /tmp a
"""

SYSCONFIG_TEXT = """\
XROOTD_USER=xrootd
XROOTD_GROUP=xrootd

XROOTD_DEFAULT_OPTIONS="-l /var/log/xrootd/xrootd.log -c /etc/xrootd/xrootd-standalone.cfg -k fifo"
CMSD_DEFAULT_OPTIONS="-l /var/log/xrootd/cmsd.log -c /etc/xrootd/xrootd-standalone.cfg -k fifo"
PURD_DEFAULT_OPTIONS="-l /var/log/xrootd/purged.log -c /etc/xrootd/xrootd-standalone.cfg -k fifo"
XFRD_DEFAULT_OPTIONS="-l /var/log/xrootd/xfrd.log -c /etc/xrootd/xrootd-standalone.cfg -k fifo"

XROOTD_INSTANCES="default"
CMSD_INSTANCES="default"
PURD_INSTANCES="default"
XFRD_INSTANCES="default"
"""


class TestStartXrootd(osgunittest.OSGTestCase):

    def setUp(self):
        if core.rpm_is_installed("xcache"):
            self.skip_ok_if(core.PackageVersion("xcache") >= "1.0.2",
                            "xcache 1.0.2+ configs conflict with xrootd tests")

    def test_01_configure_xrootd(self):
        core.config['xrootd.pid-file'] = '/var/run/xrootd/xrootd-default.pid'
        core.config['certs.xrootdcert'] = '/etc/grid-security/xrd/xrdcert.pem'
        core.config['certs.xrootdkey'] = '/etc/grid-security/xrd/xrdkey.pem'
        if core.rpm_is_installed('osg-xrootd-standalone'):
            # rootdir and resourcename needs to be set early for the default osg-xrootd config
            core.config['xrootd.config'] = '/etc/xrootd/config.d/10-osg-test.cfg'
        else:
            core.config['xrootd.config'] = '/etc/xrootd/config.d/99-osg-test.cfg'
        core.config['xrootd.service-defaults'] = '/etc/sysconfig/xrootd'
        core.config['xrootd.multiuser'] = False
        core.state['xrootd.started-server'] = False
        core.state['xrootd.backups-exist'] = False

        self.skip_ok_unless(core.options.adduser, 'user not created')
        core.skip_ok_unless_installed('xrootd', 'globus-proxy-utils', by_dependency=True)

        user = pwd.getpwnam("xrootd")
        core.install_cert('certs.xrootdcert', 'certs.hostcert', 'xrootd', 0o644)
        core.install_cert('certs.xrootdkey', 'certs.hostkey', 'xrootd', 0o400)

        if core.rpm_is_installed('osg-xrootd-standalone'):
            core.log_message("Using osg-xrootd configuration")
            xrootd_config = META_XROOTD_CFG_TEXT
        else:
            lcmaps_packages = ('lcmaps', 'lcmaps-db-templates', 'xrootd-lcmaps', 'vo-client', 'vo-client-lcmaps-voms')
            if all([core.rpm_is_installed(x) for x in lcmaps_packages]):
                core.log_message("Using xrootd-lcmaps authentication")
                sec_protocol = '-authzfun:libXrdLcmaps.so -authzfunparms:loglevel=5,policy=authorize_only'
            else:
                core.log_message("Using XRootD mapfile authentication")
                sec_protocol = '-gridmap:/etc/grid-security/xrd/xrdmapfile'
                files.write("/etc/grid-security/xrd/xrdmapfile", "\"%s\" vdttest" % core.config['user.cert_subject'],
                            owner="xrootd",
                            chown=(user.pw_uid, user.pw_gid))
            xrootd_config = XROOTD_CFG_TEXT % sec_protocol

        files.write(core.config['xrootd.config'], xrootd_config, owner='xrootd', backup=True, chmod=0o644)

        if core.el_release() < 7:
            files.write(core.config['xrootd.service-defaults'], SYSCONFIG_TEXT,
                        owner="xrootd", chown=(user.pw_uid, user.pw_gid), chmod=0o644)

        authfile = '/etc/xrootd/auth_file'
        files.write(authfile, AUTHFILE_TEXT, owner="xrootd", chown=(user.pw_uid, user.pw_gid))

        core.state['xrootd.backups-exist'] = True

    def test_02_configure_hdfs(self):
        core.skip_ok_unless_installed('xrootd-hdfs')
        hdfs_config = "ofs.osslib /usr/lib64/libXrdHdfs.so"
        files.append(core.config['xrootd.config'], hdfs_config, backup=False)

    def test_03_configure_multiuser(self):
        core.skip_ok_unless_installed('xrootd-multiuser', 'globus-proxy-utils', by_dependency=True)
        xrootd_multiuser_conf = "xrootd.fslib libXrdMultiuser.so default"
        files.append(core.config['xrootd.config'], xrootd_multiuser_conf, owner='xrootd', backup=False)
        core.config['xrootd.multiuser'] = True

    def test_04_start_xrootd(self):
        core.skip_ok_unless_installed('xrootd', 'globus-proxy-utils', by_dependency=True)
        if core.el_release() < 7:
            core.config['xrootd_service'] = "xrootd"
        elif core.config['xrootd.multiuser']:
            core.config['xrootd_service'] = "xrootd-privileged@standalone"
        else:
            core.config['xrootd_service'] = "xrootd@standalone"

        service.check_start(core.config['xrootd_service'])
        core.state['xrootd.started-server'] = True
