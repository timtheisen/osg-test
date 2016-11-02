import os
import pwd
import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest

class TestMyProxy(osgunittest.OSGTestCase):

    def test_01_remove_proxy(self):
        core.skip_ok_unless_installed('myproxy', 'myproxy-server')
        self.skip_ok_unless(core.state['myproxy.started-server'], 'MyProxy server failed to start')
        # If there is no pre-existing proxy file, the following command will
        # produce error output and have exit status 1; because this is the
        # expected (but not the only valid) case, do not check the output or
        # exit status.  This test exists only to clear out a pre-existing proxy.
        command = ('myproxy-destroy', '--verbose', '-s', core.get_hostname(), '-l', core.options.username)
        core.system(command, user=True)

    def test_02_check_usercert_pass(self):
        core.skip_ok_unless_installed('globus-proxy-utils', 'myproxy', 'myproxy-server')
        self.skip_ok_unless(core.state['myproxy.started-server'], 'MyProxy server failed to start')

        user = pwd.getpwnam(core.options.username)
        userkey = os.path.join(user.pw_dir, '.globus', 'userkey.pem')
        command = ('openssl', 'rsa', '-in', userkey, '-passin', 'pass:', '-text')
        exit_status, _, _ = core.system(command, user=True)
        if exit_status == 0:
            core.system(('grid-proxy-destroy',), user=True)
            self.fail('user cert has no password')

    def test_03_proxypath(self):
        # Grab the path of the proxy created for the proxy test
        core.skip_ok_unless_installed('globus-proxy-utils', 'myproxy', 'myproxy-server')
        self.skip_ok_unless(core.state['myproxy.started-server'], 'MyProxy server failed to start')

        command = ('grid-proxy-info', '-path')
        _, proxypath, _ = core.system(command, user=True)
        core.state['proxy.path'] = proxypath.split('\n')[0]

    def test_04_myproxy_init(self):
        core.skip_ok_unless_installed('myproxy', 'myproxy-server')
        self.skip_bad_unless(core.state['myproxy.started-server'], 'MyProxy server failed to start')

        core.state['myproxy.created'] = False
        core.config['myproxy.password'] = 'Myosgproxy!'
        core.skip_ok_unless_installed('myproxy', 'myproxy-server')
        # The -S option is given in the command so it accepts the stdin input for the passowrds
        command = ('myproxy-init', '--verbose', '-C', core.state['proxy.path'], '-y', core.state['proxy.path'],
                   '-s', core.get_hostname(), '-S', '-l', core.options.username)
        # We give an already created proxy to my proxy and password to store it
        password = core.config['myproxy.password']
        core.check_system(command, 'Normal myproxy-init', user=True, stdin=password)
        core.state['myproxy.created'] = True

    def test_05_my_proxy_retrieval(self):
        core.skip_ok_unless_installed('myproxy', 'myproxy-server')
        self.skip_bad_unless(core.state['myproxy.started-server'], 'MyProxy server failed to start')
        self.skip_bad_unless(core.state['myproxy.created'], 'MyProxy creation failed')

        command = ('myproxy-logon', '--verbose', '-s', core.get_hostname(), '-l', core.options.username)
        password = core.config['myproxy.password'] + '\n'
        core.check_system(command, 'myproxy-logon retrieval', user=True, stdin=password)
