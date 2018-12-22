import os
import shutil

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.tomcat as tomcat
import osgtest.library.osgunittest as osgunittest

class TestStopTomcat(osgunittest.OSGTestCase):

    def test_01_stop_tomcat(self):
        core.skip_ok_unless_installed(tomcat.pkgname())
        self.skip_bad_unless(core.state['tomcat.started'], 'Tomcat not started')
        service.check_stop(tomcat.pkgname())

    def test_03_deconfig_tomcat_properties(self):
        core.skip_ok_unless_installed(tomcat.pkgname(), 'gratia-service')
        files.restore(os.path.join(tomcat.sysconfdir(), 'server.xml'), 'gratia')

    def test_04_deconfig_catalina_logging(self):
        core.skip_ok_unless_installed(tomcat.pkgname())
        files.restore(core.config['tomcat.logging-conf'], 'tomcat')

    def test_05_deconfig_context(self):
        core.skip_ok_unless_installed(tomcat.pkgname())
        self.skip_ok_if(core.options.nightly, 'Allow persistence in the nightlies')
        files.restore(tomcat.contextfile(), 'tomcat')

    def test_07_deconfig_tomcat(self):
        core.skip_ok_unless_installed(tomcat.pkgname())

        files.restore(tomcat.conffile(), 'tomcat')
