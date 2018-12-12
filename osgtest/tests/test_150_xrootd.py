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
        core.config['xrootd.multiuser'] = "OFF"
        core.state['xrootd.started-server'] = False
        core.state['xrootd.backups-exist'] = False

        self.skip_ok_unless(core.options.adduser, 'user not created')
        core.skip_ok_unless_installed('xrootd', by_dependency=True)

        user = pwd.getpwnam("xrootd")
        if core.config['xrootd.gsi'] == "ON":
            core.skip_ok_unless_installed('globus-proxy-utils')
            core.install_cert('certs.xrootdcert', 'certs.hostcert', 'xrootd', 0o644)
            core.install_cert('certs.xrootdkey', 'certs.hostkey', 'xrootd', 0o400)

            lcmaps_packages = ('lcmaps', 'lcmaps-db-templates', 'xrootd-lcmaps', 'vo-client', 'vo-client-lcmaps-voms')
            if all([core.rpm_is_installed(x) for x in lcmaps_packages]):
                core.log_message("Using xrootd-lcmaps authentication")
                sec_protocol = '-authzfun:libXrdLcmaps.so -authzfunparms:--loglevel,5'
                if core.package_version_compare('xrootd-lcmaps', '1.4.0') >= 0:
                    sec_protocol += ',--policy,authorize_only'
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

    def test_03_configure_multiuser(self):
        core.skip_ok_unless_installed('xrootd-multiuser')
        core.config['xrootd.multiuser'] = "ON"
        # We need both multiuser and gsi part to test multiuser
        if core.config['xrootd.multiuser'] == "ON" and core.config['xrootd.gsi'] == "ON":
           xrootd_multiuser_conf = "xrootd.fslib libXrdMultiuser.so default"
           files.append(core.config['xrootd.config'], xrootd_multiuser_conf, owner='xrootd', backup=False)
      
    def test_04_start_xrootd(self):
        core.skip_ok_unless_installed('xrootd', by_dependency=True)
        if core.el_release() < 7:
            core.config['xrootd_service'] = "xrootd"
        elif core.config['xrootd.multiuser'] == "ON":
            core.config['xrootd_service'] = "xrootd-privileged@clustered"
        else:
            core.config['xrootd_service'] = "xrootd@clustered"

        service.check_start(core.config['xrootd_service'])
        core.state['xrootd.started-server'] = True
