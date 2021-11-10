import os
import pwd
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest
import osgtest.library.voms as voms
import osgtest.library.xrootd as xrootd
import shlex
import shutil
import time


XROOTD5_SCITOKENS_CFG_TXT = """
# Allow scitokens on all ports, all protocols
ofs.authlib ++ libXrdAccSciTokens.so config=%s

# Pass the bearer token to the Xrootd authorization framework.
http.header2cgi Authorization authz

# Allow using tokens with strong auth
sec.protocol ztn
"""

# XRootD configuration necessary for osg-xrootd-standalone
STANDALONE_XROOTD_CFG_TEXT = f"""\
set rootdir = {xrootd.ROOTDIR}
set resourcename = OSG_TEST_XROOTD_STANDALONE
"""
STANDALONE_XROOTD_FOR_3_5_CFG_TEXT = """
xrd.tls /etc/grid-security/xrd/xrdcert.pem /etc/grid-security/xrd/xrdkey.pem
xrd.tlsca noverify
acc.authdb /etc/xrootd/Authfile
ofs.authorize
xrootd.seclib /usr/lib64/libXrdSec.so
"""

# Authfile syntax is described in https://xrootd.slac.stanford.edu/doc/dev50/sec_config.htm#_Toc64492263
# Privileges used are "a" (all) and "rl" (read only).
# All paths are relative to the rootdir defined above
AUTHFILE_TEXT = f"""\
# A user has full privileges to a directory named after them (e.g. matyas has /matyas/, vdttest has /vdttest/)
u =      /@=/ a

# Our test VO has full privileges to /osgtestvo
g /{voms.VONAME} /{voms.VONAME}/ a

# All users (including unauth users) have full privileges to /public/
u *      /public/ a
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
        core.config['xrootd.security'] = set()
        core.config['certs.xrootdcert'] = '/etc/grid-security/xrd/xrdcert.pem'
        core.config['certs.xrootdkey'] = '/etc/grid-security/xrd/xrdkey.pem'
        # rootdir and resourcename needs to be set early for the default osg-xrootd config
        core.config['xrootd.config'] = '/etc/xrootd/config.d/10-osg-test.cfg'
        core.config['xrootd.logging-config'] = '/etc/xrootd/config.d/99-logging.cfg'
        core.config['xrootd.service-defaults'] = '/etc/sysconfig/xrootd'
        core.config['xrootd.multiuser'] = False
        core.state['xrootd.backups-exist'] = False
        core.state['xrootd.had-failures'] = False
        core.config['xrootd.public_subdir'] = "public"
        core.config['xrootd.user_subdir'] = core.options.username
        core.config['xrootd.vo_subdir'] = voms.VONAME
        self.skip_ok_unless(core.state['user.verified'], "Test user not available")

        xrootd_user = pwd.getpwnam("xrootd")

        xrootd_config = STANDALONE_XROOTD_CFG_TEXT

        if core.osg_release() < '3.6':
            xrootd_config += STANDALONE_XROOTD_FOR_3_5_CFG_TEXT

        if core.dependency_is_installed("globus-proxy-utils") or core.dependency_is_installed("voms-clients"):
            core.config['xrootd.security'].add("GSI")
        if core.dependency_is_installed("xrootd-scitokens"):
            core.config['xrootd.security'].add("SCITOKENS")
        if voms.is_installed():
            core.config['xrootd.security'].add("VOMS")

        self.skip_ok_unless(core.config['xrootd.security'], "No xrootd security available")

        core.install_cert('certs.xrootdcert', 'certs.hostcert', 'xrootd', 0o644)
        core.install_cert('certs.xrootdkey', 'certs.hostkey', 'xrootd', 0o400)

        files.write(core.config['xrootd.logging-config'], XROOTD_LOGGING_CFG_TEXT, owner='xrootd', backup=True, chmod=0o644)
        files.write(core.config['xrootd.config'], xrootd_config, owner='xrootd', backup=True, chmod=0o644)

        authfile = '/etc/xrootd/Authfile'
        files.write(authfile, AUTHFILE_TEXT, owner="xrootd", chown=(xrootd_user.pw_uid, xrootd_user.pw_gid), chmod=0o644)
        try:
            shutil.rmtree(xrootd.ROOTDIR)
        except FileNotFoundError:
            pass
        public_dir = f"{xrootd.ROOTDIR}/{core.config['xrootd.public_subdir']}"
        files.safe_makedirs(xrootd.ROOTDIR)
        os.chmod(xrootd.ROOTDIR, 0o755)
        files.safe_makedirs(public_dir)
        os.chmod(public_dir, 0o1777)
        user_dir = f"{xrootd.ROOTDIR}/{core.config['xrootd.user_subdir']}"
        files.safe_makedirs(user_dir)
        os.chmod(user_dir, 0o770)
        vo_dir = f"{xrootd.ROOTDIR}/{core.config['xrootd.vo_subdir']}"
        files.safe_makedirs(vo_dir)
        os.chmod(vo_dir, 0o1777)
        core.system(["chown", "-R", "xrootd:xrootd", xrootd.ROOTDIR])
        os.chown(user_dir, core.state["user.uid"], xrootd_user.pw_gid)

        core.check_system(["find", xrootd.ROOTDIR, "-ls"], f"Couldn't dump contents of {xrootd.ROOTDIR}")

        core.state['xrootd.backups-exist'] = True
        core.state['xrootd.is-configured'] = True

    # Make sure the directories are set up correctly and that the xrootd user
    # can access everything it's supposed to be able to.
    # TODO: Remove before merging into master
    def test_02_xrootd_user_file_access(self):
        self.skip_ok_unless(core.state['xrootd.is-configured'], "xrootd is not configured")
        public_subdir = core.config['xrootd.public_subdir']
        xrootd_user = pwd.getpwnam("xrootd")
        # Verify xrootd user permissions
        testfile1 = os.path.join(xrootd.ROOTDIR, "plain_copy_xrootd_rootdir")
        testfile2 = os.path.join(xrootd.ROOTDIR, public_subdir, "plain_copy_xrootd_public")
        # Set GID first: if I set UID first I won't have permissions to set GID
        os.setegid(xrootd_user.pw_gid)
        try:
            os.seteuid(xrootd_user.pw_uid)
            try:
                try:
                    with open(testfile1, "w") as fh:
                        fh.write("hello")
                except OSError as err:
                    self.fail(f"xrootd user cannot access {testfile1}: {err}")
                try:
                    with open(testfile2, "w") as fh:
                        fh.write("world")
                except OSError as err:
                    self.fail(f"xrootd user cannot access {testfile2}: {err}")
            finally:
                os.seteuid(os.getuid())
        finally:
            os.setegid(os.getgid())

    # Make sure the directories are set up correctly and that the test user
    # can access everything it's supposed to be able to.
    # TODO: Remove before merging into master
    def test_03_test_user_file_access(self):
        self.skip_ok_unless(core.state['xrootd.is-configured'], "xrootd is not configured")
        username = core.options.username
        public_subdir = core.config['xrootd.public_subdir']
        user_subdir = core.config['xrootd.user_subdir']
        # Verify unpriv user permissions
        testfile3 = os.path.join(xrootd.ROOTDIR, user_subdir, "plain_copy_testuser_user")
        testfile4 = os.path.join(xrootd.ROOTDIR, public_subdir, "plain_copy_testuser_public")
        # Set GID first: if I set UID first I won't have permissions to set GID
        os.setegid(core.state['user.gid'])
        try:
            os.seteuid(core.state['user.uid'])
            try:
                try:
                    with open(testfile3, "w") as fh:
                        fh.write("hello")
                except OSError as err:
                    self.fail(f"{username} user cannot access {testfile3}: {err}")
                try:
                    with open(testfile4, "w") as fh:
                        fh.write("world")
                except OSError as err:
                    self.fail(f"{username} user cannot access {testfile4}: {err}")
            finally:
                os.seteuid(os.getuid())
        finally:
            os.setegid(os.getgid())

    @core.osgrelease(3.5)
    def test_04_configure_hdfs(self):
        core.skip_ok_unless_installed('xrootd-hdfs')
        hdfs_config = "ofs.osslib /usr/lib64/libXrdHdfs.so\n"
        files.append(core.config['xrootd.config'], hdfs_config, backup=False)

    def test_05_configure_multiuser(self):
        core.skip_ok_unless_installed('xrootd-multiuser', by_dependency=True)
        if core.PackageVersion("xrootd-multiuser") < "1.0.0-0":
            xrootd_multiuser_conf = "xrootd.fslib libXrdMultiuser.so default\n"
        else:
            xrootd_multiuser_conf = "ofs.osslib ++ libXrdMultiuser.so\n" \
                                    "ofs.ckslib ++ libXrdMultiuser.so\n"
        if os.path.exists("/etc/xrootd/config.d/60-osg-multiuser.cfg"):
            core.log_message("Not adding XRootD multiuser config, already exists")
        else:
            files.append(core.config['xrootd.config'], xrootd_multiuser_conf, owner='xrootd', backup=False)
        core.config['xrootd.multiuser'] = True

    def test_06_configure_scitokens(self):
        self.skip_ok_unless("SCITOKENS" in core.config['xrootd.security'], "Not using SciTokens for XRootD")
        scitokens_conf_path = "/etc/xrootd/scitokens.conf"
        files.write(scitokens_conf_path, SCITOKENS_CONF_TEXT, owner='xrootd', chmod=0o644)

        if os.path.exists("/etc/xrootd/config.d/50-osg-scitokens.cfg"):
            core.log_message("Not adding XRootD SciTokens config, already exists")
        else:
            files.append(core.config['xrootd.config'],
                         XROOTD5_SCITOKENS_CFG_TXT % scitokens_conf_path,
                         backup=False)

    def test_07_check_cconfig(self):
        xrootd_config = xrootd.cconfig("standalone", raw=False, quiet=False)
        self.assertRegexInList(xrootd_config,
                               rf"^[ ]*oss\.localroot[ ]+{xrootd.ROOTDIR}[ ]*$",
                               f"'oss.localroot {xrootd.ROOTDIR}' not found")
        self.assertRegexInList(xrootd_config,
                               r"^[ ]*acc\.authdb[ ]+/etc/xrootd/Authfile[ ]*$",
                               "'acc.authdb /etc/xrootd/Authfile' not found")
        self.assertRegexInList(xrootd_config,
                               r"^[ ]*ofs\.authorize[ ]*$",
                               "'ofs.authorize' not found")
        self.assertRegexInList(xrootd_config,
                               r"^[ ]*xrootd\.seclib[ ]+/usr/lib64/libXrdSec\.so[ ]*$",
                               "'xrootd.seclib /usr/lib64/libXrdSec.so' not found")
        if "SCITOKENS" in core.config['xrootd.security']:
            self.assertRegexInList(xrootd_config,
                                   r"^[ ]*ofs\.authlib[ ]+[+][+][ ]+libXrdAccSciTokens\.so[ ]+config=/etc/xrootd/scitokens\.conf[ ]*$",
                                   "'ofs.authlib ++ libXrdAccSciTokens.so config=/etc/xrootd/scitokens.conf' not found")

    def test_08_start_xrootd(self):
        self.skip_ok_unless(core.state['xrootd.is-configured'], "xrootd is not configured")
        if core.config['xrootd.multiuser']:
            core.config['xrootd_service'] = "xrootd-privileged@standalone"
        else:
            core.config['xrootd_service'] = "xrootd@standalone"

        core.state['xrootd.service-was-running'] = False
        # Stop the service so it gets our new config
        if service.is_running(core.config['xrootd_service']):
            core.state['xrootd.service-was-running'] = True
            service.stop(core.config['xrootd_service'], force=True)
            time.sleep(5)

        # clear the logfile so it only contains our run
        if core.options.manualrun:
            files.preserve_and_remove(xrootd.logfile("standalone"), "xrootd")
        try:
            service.check_start(core.config['xrootd_service'], min_up_time=5)
        except Exception:
            xrootd.dump_log(125, "standalone")
            raise
