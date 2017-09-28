import os
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

# ==========================================================================
# Note: March 2012 version, add checking prerequisites such as globus-proxy-utils,
# to avoid confusion.

class TestGlexec(osgunittest.OSGTestCase):

    # Constants
    __glexec_client_cert = '/tmp/x509_client_cert'

    # attributes to be filled later
    __uid = ''
    __user_proxy_path = ''

    # ==========================================================================

    def setUpClass(self):
        # glexec not available in 3.4
        self.skip_ok_if(core.osg_release())


    def test_01_configure_lcmaps(self):
        core.state['glexec.lcmaps_written'] = False
        core.skip_ok_unless_installed('glexec', 'lcmaps-plugins-basic')
        # Use the lcmaps.db.gridmap.glexec template from OSG 3.3
        template = '''glexectracking = "lcmaps_glexec_tracking.mod"
                 "-exec /usr/sbin/glexec_monitor"

gridmapfile = "lcmaps_localaccount.mod"
              "-gridmap /etc/grid-security/grid-mapfile"

verifyproxy = "lcmaps_verify_proxy.mod"
              "--allow-limited-proxy"
              " -certdir /etc/grid-security/certificates"

good        = "lcmaps_dummy_good.mod"
bad         = "lcmaps_dummy_bad.mod"

authorize_only:
gridmapfile -> good | bad

glexec:
verifyproxy -> gridmapfile
gridmapfile -> glexectracking
'''
        files.write(core.config['lcmaps.db'], template, owner='glexec')
        core.state['glexec.lcmaps_written'] = True

    def test_02_define_user_proxy_path(self):
        core.skip_ok_unless_installed('glexec')
        command = ('/usr/bin/id', '-u')
        _, stdout, _ = core.system(command, True)
        TestGlexec.__uid = stdout.rstrip()
        TestGlexec.__user_proxy_path = '/tmp/x509up_u'+self.__uid

    def test_03_create_user_proxy(self):
        core.skip_ok_unless_installed('globus-proxy-utils')
        self.skip_ok_if(self.__user_proxy_path == '', "User proxy path does not exist.")

        # OK, software is present, now just check it previous tests did create the proxy already so
        # we don't do it twice
        command = ('grid-proxy-info', '-f', self.__user_proxy_path)
        status, _, _ = core.system(command, True)

        if int(status) != 0: # no proxy found for some reason, try to construct a new one
            command = ('grid-proxy-init', '-out', self.__user_proxy_path)
            password = core.options.password + '\n'
            status, _, _ = core.system(command, True, password)
            self.assert_(status == 0, 'grid-proxy-init for user ' +core.options.username +
                         ' has failed even though globus-proxy-util was present')

        # we need to have the right permissions on that proxy for glexec to agree to work,
        # and the easiest way is to copy the file
        command = ('/bin/cp', self.__user_proxy_path, self.__glexec_client_cert)
        status, _, _ = core.system(command)
        os.environ['GLEXEC_CLIENT_CERT'] = self.__glexec_client_cert

    def test_04_glexec_switch_id(self):
        core.skip_ok_unless_installed('glexec', 'globus-proxy-utils')
        command = ('grid-proxy-info', '-f', self.__user_proxy_path)
        status, stdout, _ = core.system(command, True)

        if int(status) != 0: # no proxy found even after previous checks, have to skip
            self.skip_bad('suitable proxy not found')
            return

        command = ('/usr/sbin/glexec', '/usr/bin/id', '-u')

        status, stdout, _ = core.system(command)
        switched_id = stdout.rstrip()

        self.assert_(self.__uid == switched_id,
                     'Glexec identity switch from root to user ' + core.options.username + ' failed')

    def test_05_glexec_proxy_cleanup(self):
        core.skip_ok_unless_installed('glexec', 'globus-proxy-utils')

        try:
            os.unlink(self.__glexec_client_cert)
        except:
            pass


    def test_06_restore_lcmaps(self):
        core.skip_ok_unless_installed('glexec', 'lcmaps-plugins-basic')
        self.skip_ok_unless(core.state['glexec.lcmaps_written'], 'did not write lcmaps.db for glexec tests')
        files.restore(core.config['lcmaps.db'], 'glexec')
