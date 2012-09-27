import os
import pwd
import shutil
import osgtest.library.core as core
import osgtest.library.files as files
import unittest

class TestStartXrootd(unittest.TestCase):
    def install_cert(self, target_key, source_key, owner_name, permissions):
        target_path = core.config[target_key]
        target_dir = os.path.dirname(target_path)
        source_path = core.config[source_key]
        user = pwd.getpwnam(owner_name)

        if os.path.exists(target_path):
            backup_path = target_path + '.osgtest.backup'
            shutil.move(target_path, backup_path)
            core.state[target_key + '-backup'] = backup_path

        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
            core.state[target_key + '-dir'] = target_dir
            os.chown(target_dir, user.pw_uid, user.pw_gid)
            os.chmod(target_dir, 0755)

        shutil.copy(source_path, target_path)
        core.state[target_key] = target_path
        os.chown(target_path, user.pw_uid, user.pw_gid)
        os.chmod(target_path, permissions)

    def test_01_start_xrootd(self):
        core.config['xrootd.pid-file']='/var/run/xrootd/xrootd-default.pid'
        core.config['certs.hostcert'] = '/etc/grid-security/hostcert.pem'
        core.config['certs.hostkey'] = '/etc/grid-security/hostkey.pem'
        core.config['certs.xrootdcert']='/etc/grid-security/xrd/xrdcert.pem'
        core.config['certs.xrootdkey']='/etc/grid-security/xrd/xrdkey.pem'
        core.config['xrootd.gsi']="ON"
        core.state['xrootd.started-server'] = False

        if not core.rpm_is_installed('xrootd-server'):
            core.skip('not installed')
            return

        if core.el_release()==6:
            core.log_message("GSI disabled on RHEL6 variants (openssl1.0 bug)")
            core.config['xrootd.gsi']="OFF"


        if core.config['xrootd.gsi'] == "ON":
            self.install_cert('certs.xrootdcert', 'certs.hostcert', 
                'xrootd', 0644)
            self.install_cert('certs.xrootdkey', 'certs.hostkey', 
                'xrootd', 0400)

            cfgfile='/etc/xrootd/xrootd-clustered.cfg'
            cfgtext='cms.space min 2g 5g\n'
            cfgtext=cfgtext+'xrootd.seclib /usr/lib64/libXrdSec.so\n'
            cfgtext=cfgtext+'sec.protocol /usr/lib64 gsi -certdir:/etc/grid-security/certificates -cert:/etc/grid-security/xrd/xrdcert.pem -key:/etc/grid-security/xrd/xrdkey.pem -crl:3 -gridmap:/etc/grid-security/xrd/xrdmapfile --gmapopt:10 --gmapto:0\n'
            cfgtext=cfgtext+'acc.authdb /etc/xrootd/auth_file\n'
            cfgtext=cfgtext+'ofs.authorize\n'
            files.append(cfgfile,cfgtext,owner='xrootd',backup=True)
            authfile='/etc/xrootd/auth_file'
            files.write(authfile,'u * /tmp lr\nu = /tmp/@=/ a\nu xrootd /tmp a\n',owner="xrootd")
            files.write("/etc/grid-security/xrd/xrdmapfile","\"/O=Grid/OU=GlobusTest/OU=VDT/CN=VDT Test\" vdttest",owner="xrootd")

        command = ('service', 'xrootd', 'start')
        stdout, stderr, fail = core.check_system(command, 'Start Xrootd server')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(os.path.exists(core.config['xrootd.pid-file']),
                     'xrootd server PID file missing')
        core.state['xrootd.started-server'] = True
