import os
import osgtest.library.core as core
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
        core.config['certs.xrootdcert']='/etc/grid-security/xrd/xrdcert.pem'
        core.config['certs.xrootdkey']='/etc/grid-security/xrd/xrdkey.pem'
        core.state['xrootd.started-server'] = False

        if not core.rpm_is_installed('xrootd-server'):
            core.skip('not installed')
            return

        self.install_cert('certs.xrootdcert', 'certs.hostcert', 'xrootd', 0644
)
        self.install_cert('certs.xrootdkey', 'certs.hostkey', 'xrootd', 0400)

        cfgfile='/etc/xrootd/xrootd-clustered.cfg'
        files.append(cfgfile,'cms.space min 2g 5g')
        files.append(cfgfile,'xrootd.seclib /usr/lib64/libXrdSec.so')
        files.append(cfgfile,'sec.protocol /usr/lib64 gsi -certdir:/etc/grid-security/certificates -cert:/etc/grid-security/xrd/xrdcert.pem -key:/etc/grid-security/xrd/xrdkey.pem -crl:3 -gridmap:/etc/grid-security/grid-mapfile --gmapopt:10 --gmapto:0')
        files.append(cfgfile,'acc.authdb /etc/xrootd/auth_file')
        authfile='/etc/xrootd/auth_file'
        files.write(authfile,'u * /data/xrootdfs lr',owner=xrootd)
        files.append(authfile,'u = /data/xrootdfs/@=/ a')
        files.append(authfile,'u xrootd /data/xrootdfs a')

        command = ('service', 'xrootd', 'start')
        stdout, stderr, fail = core.check_system(command, 'Start Xrootd server')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(os.path.exists(core.config['xrootd.pid-file']),
                     'xrootd server PID file missing')
        core.state['xrootd.started-server'] = True
