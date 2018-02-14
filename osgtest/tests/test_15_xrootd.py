import os
import pwd
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest

XROOTD_CFG_TEXT = """\
cms.space min 2g 5g
xrootd.seclib /usr/lib64/libXrdSec-4.so
sec.protocol /usr/lib64 gsi -certdir:/etc/grid-security/certificates \
    -cert:/etc/grid-security/xrd/xrdcert.pem \
    -key:/etc/grid-security/xrd/xrdkey.pem \
    -crl:3 \
    --gmapopt:10 \
    --gmapto:0 \
    %s
acc.authdb /etc/xrootd/auth_file
ofs.authorize
"""

AUTHFILE_TEXT = """\
u * /tmp a
u = /tmp/@=/ a
u xrootd /tmp a
"""

class TestStartXrootd(osgunittest.OSGTestCase):

    def test_01_start_xrootd(self):
        core.config['xrootd.pid-file'] = '/var/run/xrootd/xrootd-default.pid'
        core.config['certs.xrootdcert'] = '/etc/grid-security/xrd/xrdcert.pem'
        core.config['certs.xrootdkey'] = '/etc/grid-security/xrd/xrdkey.pem'
        core.config['xrootd.config'] = '/etc/xrootd/xrootd-clustered.cfg'
        core.config['xrootd.gsi'] = "ON"
        core.state['xrootd.started-server'] = False
        core.state['xrootd.backups-exist'] = False

        self.skip_ok_unless(core.options.adduser, 'user not created')
        vdt_pw = pwd.getpwnam(core.options.username)
        core.config['certs.usercert'] = os.path.join(vdt_pw.pw_dir, '.globus', 'usercert.pem')
        core.skip_ok_unless_installed('xrootd', by_dependency=True)

        user = pwd.getpwnam("xrootd")
        if core.config['xrootd.gsi'] == "ON":
            core.skip_ok_unless_installed('globus-proxy-utils')
            core.install_cert('certs.xrootdcert', 'certs.hostcert', 'xrootd', 0644)
            core.install_cert('certs.xrootdkey', 'certs.hostkey', 'xrootd', 0400)

            lcmaps_packages = ('lcmaps', 'lcmaps-db-templates', 'xrootd-lcmaps', 'vo-client', 'vo-client-lcmaps-voms')
            if all([core.rpm_is_installed(x) for x in lcmaps_packages]):
                core.log_message("Using xrootd-lcmaps authentication")
                sec_protocol = '-authzfun:libXrdLcmaps.so -authzfunparms:--loglevel,5'
            else:
                core.log_message("Using XRootD mapfile authentication")
                sec_protocol = '-gridmap:/etc/grid-security/xrd/xrdmapfile'
                files.write("/etc/grid-security/xrd/xrdmapfile", "\"%s\" vdttest" % core.config['user.cert_subject'],
                            owner="xrootd",
                            chown=(user.pw_uid, user.pw_gid))

            files.append(core.config['xrootd.config'], XROOTD_CFG_TEXT % sec_protocol, owner='xrootd', backup=True)
            authfile = '/etc/xrootd/auth_file'
            files.write(authfile, AUTHFILE_TEXT, owner="xrootd", chown=(user.pw_uid, user.pw_gid))

            core.state['xrootd.backups-exist'] = True

    def test_02_configure_hdfs(self):
        core.skip_ok_unless_installed('xrootd-hdfs')
        hdfs_config = "ofs.osslib /usr/lib64/libXrdHdfs.so"
        files.append(core.config['xrootd.config'], hdfs_config, backup=False)

    def test_03_start_xrootd(self):
        core.skip_ok_unless_installed('xrootd', by_dependency=True)
        if core.el_release() < 7:
            core.config['xrootd_service'] = "xrootd"
        else:
            core.config['xrootd_service'] = "xrootd@clustered"

        service.check_start(core.config['xrootd_service'])
        core.state['xrootd.started-server'] = True
