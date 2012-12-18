import os
import pwd
import shutil
import osgtest.library.core as core
import osgtest.library.files as files
import unittest
import re

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
        core.state['xrootd.backups-exist'] = False
        
        vdt_pw = pwd.getpwnam(core.options.username)
        core.config['certs.usercert'] = os.path.join(vdt_pw.pw_dir,
                                                     '.globus',
                                                     'usercert.pem')
        if not core.rpm_is_installed('xrootd-server'):
            core.skip('not installed')
            return
                  
        xrootd_server_version, _, _ = core.check_system(('rpm', '-q', 'xrootd-server', '--qf=%{VERSION}'), 'Getting xrootd-server version')
        
        user = pwd.getpwnam("xrootd")
        if core.config['xrootd.gsi'] == "ON":
            if not core.rpm_is_installed('globus-proxy-utils'):
              core.skip('grid-proxy-utils not installed')
              return
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
            files.write(authfile,'u * /tmp a\nu = /tmp/@=/ a\nu xrootd /tmp a\n',owner="xrootd")
            os.chown(authfile, user.pw_uid, user.pw_gid)
            
            user_dn = core.certificate_info(core.config['certs.usercert'])[1]
            files.write("/etc/grid-security/xrd/xrdmapfile","\"%s\" vdttest" % user_dn,owner="xrootd")
            os.chown("/etc/grid-security/xrd/xrdmapfile",
                user.pw_uid, user.pw_gid)
            core.state['xrootd.backups-exist'] = True

        command = ('service', 'xrootd', 'start')

        status, stdout, _ = core.system(command)
        
        is_failure_expected = (core.el_release() == 6 and
                               stdout.find('Starting xrootd (xrootd, default)') != -1 and
                               re.match(r"3\.2\.[0-5]", xrootd_server_version)) 

        if status != 0 and is_failure_expected:
            core.log_message('Expected failure on el6 with this version of xrootd-server')
            return
        elif status == 0 and is_failure_expected:
            self.fail('Unexpected success on el6 with this version of xrootd-server')

        self.assertEqual(status, 0, 'Start Xrootd server exited %d' % status)

        self.assert_(stdout.find('FAILED') == -1, 'Start Xrootd server failed')
        self.assert_(os.path.exists(core.config['xrootd.pid-file']),
                     'xrootd server PID file missing')
        core.state['xrootd.started-server'] = True

