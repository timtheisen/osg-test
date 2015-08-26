import os
import pwd
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.certificates as certs
import unittest
import re

XROOTD_CFG_TEXT = """\
cms.space min 2g 5g
xrootd.seclib /usr/lib64/libXrdSec.so
sec.protocol /usr/lib64 gsi -certdir:/etc/grid-security/certificates -cert:/etc/grid-security/xrd/xrdcert.pem -key:/etc/grid-security/xrd/xrdkey.pem -crl:3 -gridmap:/etc/grid-security/xrd/xrdmapfile --gmapopt:10 --gmapto:0
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
        core.config['xrootd.pid-file']='/var/run/xrootd/xrootd-default.pid'
        core.config['certs.hostcert'] = '/etc/grid-security/hostcert.pem'
        core.config['certs.hostkey'] = '/etc/grid-security/hostkey.pem'
        core.config['certs.xrootdcert'] = '/etc/grid-security/xrd/xrdcert.pem'
        core.config['certs.xrootdkey'] = '/etc/grid-security/xrd/xrdkey.pem'
        core.config['xrootd.gsi'] = "ON"
        core.state['xrootd.started-server'] = False
        core.state['xrootd.backups-exist'] = False
        
        vdt_pw = pwd.getpwnam(core.options.username)
        core.config['certs.usercert'] = os.path.join(vdt_pw.pw_dir, '.globus', 'usercert.pem')
        core.skip_ok_unless_installed('xrootd', by_dependency=True)
                  
        # Determine xrootd package name
        if core.rpm_is_installed('xrootd4'):
            core.config['xrootd.package'] = 'xrootd4'
        elif core.rpm_is_installed('xrootd'):
            core.config['xrootd.package'] = 'xrootd'
        
        user = pwd.getpwnam("xrootd")
        if core.config['xrootd.gsi'] == "ON":
            core.skip_ok_unless_installed('globus-proxy-utils')
            certs.install_cert('certs.xrootdcert', 'certs.hostcert', 'xrootd', 0644)
            certs.install_cert('certs.xrootdkey', 'certs.hostkey', 'xrootd', 0400)

            cfgfile = '/etc/xrootd/xrootd-clustered.cfg'
            files.append(cfgfile, XROOTD_CFG_TEXT, owner='xrootd', backup=True)
            authfile = '/etc/xrootd/auth_file'
            files.write(authfile, AUTHFILE_TEXT, owner="xrootd", chown=(user.pw_uid, user.pw_gid))
            
            user_dn = certs.certificate_info(core.config['certs.usercert'])[1]
            files.write("/etc/grid-security/xrd/xrdmapfile","\"%s\" vdttest" % user_dn, owner="xrootd",
                        chown=(user.pw_uid, user.pw_gid))
            core.state['xrootd.backups-exist'] = True

        command = ('service', 'xrootd', 'start')
        status, stdout, _ = core.system(command)
        
        self.assertEqual(status, 0, 'Start Xrootd server exited %d' % status)

        self.assert_(stdout.find('FAILED') == -1, 'Start Xrootd server failed')
        self.assert_(os.path.exists(core.config['xrootd.pid-file']), 'xrootd server PID file missing')
        core.state['xrootd.started-server'] = True

