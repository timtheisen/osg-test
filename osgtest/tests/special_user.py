import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
from cagen import CA, certificate_info
import pwd


class TestUser(osgunittest.OSGTestCase):

    def test_01_add_user(self):
        core.state['general.user_added'] = False
        core.state['general.user_cert_created'] = False

        # Bail out if this step is not needed
        if not core.options.adduser:
            core.skip('not requested')
            return
        try:
            pwd.getpwnam(core.options.username)
        except KeyError:
            pass # expected
        else:
            core.skip('user exists')
            return

        # Add
        home_dir = core.config['user.home']
        if not os.path.isdir(home_dir):
            os.mkdir(home_dir)
        command = ('useradd', '--base-dir', home_dir, '-n', '--shell', '/bin/sh', core.options.username)
        core.check_system(command, 'Add user %s' % (core.options.username))
        core.state['general.user_added'] = True

        # Set up directories
        user = pwd.getpwnam(core.options.username)
        os.chown(user.pw_dir, user.pw_uid, user.pw_gid)
        os.chmod(user.pw_dir, 0755)

        # Set up certificate
        globus_dir = os.path.join(user.pw_dir, '.globus')
        user_cert = os.path.join(globus_dir, 'usercert.pem')
        test_ca = CA.load(core.config['certs.test-ca'])
        if not os.path.exists(user_cert):
            test_ca.usercert(core.options.username, core.options.password)
            core.state['general.user_cert_created'] = True

    def test_02_user(self):
        core.state['system.wrote_mapfile'] = False
        if core.options.skiptests:
            core.skip('no user needed')
            return
        try:
            password_entry = pwd.getpwnam(core.options.username)
        except KeyError, e:
            self.fail("User '%s' should exist but does not" % core.options.username)
        self.assert_(password_entry.pw_dir != '/', "User '%s' has home directory at '/'" % (core.options.username))
        self.assert_(os.path.isdir(password_entry.pw_dir),
                     "User '%s' missing a home directory at '%s'" % (core.options.username, password_entry.pw_dir))
        cert_path = os.path.join(password_entry.pw_dir, '.globus', 'usercert.pem')
        core.config['user.cert_subject'], core.config['user.cert_issuer'] = certificate_info(cert_path)

        # Add user to mapfile
        files.append(core.config['system.mapfile'], '"%s" %s\n' %
                     (core.config['user.cert_subject'], password_entry.pw_name),
                     owner='user')
        core.state['system.wrote_mapfile'] = True
        os.chmod(core.config['system.mapfile'], 0644)
