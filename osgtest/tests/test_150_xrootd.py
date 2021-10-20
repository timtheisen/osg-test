import os
import pwd
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest
import osgtest.library.xrootd as xrootd


XROOTD5_SCITOKENS_CFG_TXT = """
# Allow scitokens on all ports, all protocols
ofs.authlib ++ libXrdAccSciTokens.so config=%s

# Pass the bearer token to the Xrootd authorization framework.
http.header2cgi Authorization authz
"""

# XRootD configuration necessary for osg-xrootd-standalone
STANDALONE_XROOTD_CFG_TEXT = """\
set rootdir = /
set resourcename = OSG_TEST_XROOTD_STANDALONE
xrd.tls /etc/grid-security/xrd/xrdcert.pem /etc/grid-security/xrd/xrdkey.pem
xrd.tlsca noverify
acc.authdb /etc/xrootd/auth_file
ofs.authorize
"""

AUTHFILE_TEXT = """\
u * /tmp a /usr/share/ r
u = /tmp/@=/ a
u xrootd /tmp a
"""

XROOTD_LOGGING_CFG_TEXT = """\
xrootd.trace all
xrd.trace all -sched
ofs.trace all
http.trace all
"""

SCITOKENS_CONF_TEXT = f"""\
[Global]
audience = OSG_TEST

[Issuer https://demo.scitokens.org]
issuer = https://demo.scitokens.org
base_path = /
map_subject = true
"""


class TestStartXrootd(osgunittest.OSGTestCase):

    def setUp(self):
        core.skip_ok_unless_installed("xrootd", "osg-xrootd-standalone", by_dependency=True)
        if core.rpm_is_installed("xcache"):
            self.skip_ok_if(core.PackageVersion("xcache") >= "1.0.2",
                            "xcache 1.0.2+ configs conflict with xrootd tests")

    def test_01_configure_xrootd(self):
        core.state['xrootd.is-configured'] = False
        core.config['xrootd.security'] = None
        core.config['certs.xrootdcert'] = '/etc/grid-security/xrd/xrdcert.pem'
        core.config['certs.xrootdkey'] = '/etc/grid-security/xrd/xrdkey.pem'
        # rootdir and resourcename needs to be set early for the default osg-xrootd config
        core.config['xrootd.config'] = '/etc/xrootd/config.d/10-osg-test.cfg'
        core.config['xrootd.logging-config'] = '/etc/xrootd/config.d/99-logging.cfg'
        core.config['xrootd.service-defaults'] = '/etc/sysconfig/xrootd'
        core.config['xrootd.multiuser'] = False
        core.config['xrootd.ztn'] = False
        core.state['xrootd.started-server'] = False
        core.state['xrootd.backups-exist'] = False

        xrootd_config = STANDALONE_XROOTD_CFG_TEXT

        self.skip_ok_unless(core.options.adduser, 'user not created')
        if core.osg_release().version < '3.6':
            core.skip_ok_unless_installed("globus-proxy-utils")
            core.config['xrootd.security'] = "GSI"

        else:  # 3.6+
            core.skip_ok_unless_installed("xrootd-scitokens")
            core.config['xrootd.security'] = "SCITOKENS"

        user = pwd.getpwnam("xrootd")
        core.install_cert('certs.xrootdcert', 'certs.hostcert', 'xrootd', 0o644)
        core.install_cert('certs.xrootdkey', 'certs.hostkey', 'xrootd', 0o400)

        files.write(core.config['xrootd.logging-config'], XROOTD_LOGGING_CFG_TEXT, owner='xrootd', backup=True, chmod=0o644)
        files.write(core.config['xrootd.config'], xrootd_config, owner='xrootd', backup=True, chmod=0o644)

        authfile = '/etc/xrootd/auth_file'
        files.write(authfile, AUTHFILE_TEXT, owner="xrootd", chown=(user.pw_uid, user.pw_gid))

        core.state['xrootd.backups-exist'] = True
        core.state['xrootd.is-configured'] = True

    @core.osgrelease(3.5)
    def test_04_configure_hdfs(self):
        core.skip_ok_unless_installed('xrootd-hdfs')
        hdfs_config = "ofs.osslib /usr/lib64/libXrdHdfs.so"
        files.append(core.config['xrootd.config'], hdfs_config, backup=False)

    def test_05_configure_multiuser(self):
        core.skip_ok_unless_installed('xrootd-multiuser', 'globus-proxy-utils', by_dependency=True)
        if core.PackageVersion("xrootd-multiuser") < "1.0.0-0":
            xrootd_multiuser_conf = "xrootd.fslib libXrdMultiuser.so default"
        else:
            xrootd_multiuser_conf = "ofs.osslib ++ libXrdMultiuser.so\n" \
                                    "ofs.ckslib ++ libXrdMultiuser.so"
        files.append(core.config['xrootd.config'], xrootd_multiuser_conf, owner='xrootd', backup=False)
        core.config['xrootd.multiuser'] = True

    def test_06_configure_scitokens(self):
        self.skip_ok_unless(core.config['xrootd.security'] == "SCITOKENS", "Not using SciTokens for XRootD")
        scitokens_conf_path = "/etc/xrootd/scitokens.conf"
        files.write(scitokens_conf_path, SCITOKENS_CONF_TEXT, owner='xrootd', chmod=0o644)

        if os.path.exists("/etc/xrootd/config.d/50-osg-scitokens.cfg"):
            core.log_message("Not adding XRootD SciTokens config, already exists")
        else:
            files.append(core.config['xrootd.config'],
                         XROOTD5_SCITOKENS_CFG_TXT % scitokens_conf_path,
                         backup=False)

        ### ztn tests don't work right now.
        #
        # # Enable ztn which requires that the token be sent over an encrypted connection
        # # and allows getting the token from the environment.
        # core.config['xrootd.ztn'] = True
        # files.write("/etc/xrootd/config.d/99-osgtest-ztn.cfg",
        #             "sec.protocol ztn\n",
        #             chmod=0o644,
        #             owner='xrootd')

    def test_08_start_xrootd(self):
        core.skip_ok_unless_installed('xrootd', 'globus-proxy-utils', by_dependency=True)
        if core.el_release() < 7:
            core.config['xrootd_service'] = "xrootd"
        elif core.config['xrootd.multiuser']:
            core.config['xrootd_service'] = "xrootd-privileged@standalone"
        else:
            core.config['xrootd_service'] = "xrootd@standalone"

        service.check_start(core.config['xrootd_service'])
        core.state['xrootd.started-server'] = True
