import crypt
import os
import random

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
from cagen import CA, certificate_info
import pwd


def random_string(length):
    """Return a random string of the given length with each character
    from the printable ASCII range.
    """
    result = ""
    for _ in range(length):
        result += chr(random.randint(33, 126))
    return result


def encrypted_password(plaintext, salt="osgtest"):
    """Return the encrypted version of the password from the plaintext,
    suitable for directly putting into /etc/shadow or feeding it to
    useradd/usermod.
    """
    # The default salt is kinda weak, but the account should not be
    # long-lived anyway.
    return crypt.crypt(plaintext, "$6$" + salt)


class TestUser(osgunittest.OSGTestCase):

    def test_01_add_user(self):
        core.state['general.user_added'] = False

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
        # SSH requires that the user have a password - even if password
        # auth is disabled. Set a random password for the vdttest user
        password = encrypted_password(random_string(16))

        command = ('useradd', '--base-dir', home_dir, '--password', password, '--shell', '/bin/sh',
                   core.options.username)
        core.check_system(command, 'Add user %s' % core.options.username)
        core.state['general.user_added'] = True

        # Set up directories
        core.state['user.pwd'] = pwd.getpwnam(core.options.username)
        os.chown(core.state['user.pwd'].pw_dir, core.state['user.pwd'].pw_uid, core.state['user.pwd'].pw_gid)
        os.chmod(core.state['user.pwd'].pw_dir, 0o755)

    def test_02_verify_user(self):
        core.state['user.verified'] = False

        if core.options.skiptests:
            core.skip('no user needed')
            return

        try:
            user = core.state['user.pwd']
        except KeyError:
            try:
                core.state['user.pwd'] = user = pwd.getpwnam(core.options.username)
            except KeyError:
                self.fail("User '%s' should exist but does not" % core.options.username)

        self.assert_(user.pw_dir != '/', "User '%s' has home directory at '/'" % (core.options.username))
        self.assert_(os.path.isdir(user.pw_dir),
                     "User '%s' missing a home directory at '%s'" % (core.options.username, user.pw_dir))

        core.state['user.verified'] = True

    def test_03_generate_user_cert(self):
        core.state['general.user_cert_created'] = False
        core.state['system.wrote_mapfile'] = False

        if core.options.skiptests:
            core.skip('no user needed')
            return

        self.skip_bad_unless(core.state['user.verified'], "User doesn't exist, has HOME=/, or is missing HOME")

        # Set up certificate
        globus_dir = os.path.join(core.state['user.pwd'].pw_dir, '.globus')
        core.state['user.cert_path'] = os.path.join(globus_dir, 'usercert.pem')
        test_ca = CA.load(core.config['certs.test-ca'])
        if not os.path.exists(core.state['user.cert_path']):
            test_ca.usercert(core.options.username, core.options.password)
            core.state['general.user_cert_created'] = True

        (core.config['user.cert_subject'],
         core.config['user.cert_issuer']) = certificate_info(core.state['user.cert_path'])

        # Add user to mapfile
        files.append(core.config['system.mapfile'], '"%s" %s\n' %
                     (core.config['user.cert_subject'], core.state['user.pwd'].pw_name),
                     owner='user')
        core.state['system.wrote_mapfile'] = True
        os.chmod(core.config['system.mapfile'], 0o644)
