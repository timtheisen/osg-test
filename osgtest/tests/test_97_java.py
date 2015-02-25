import osgtest.library.core as core
import osgtest.library.java as java
import osgtest.library.files as files
import osgtest.library.tomcat as tomcat
import osgtest.library.osgunittest as osgunittest

class TestCleanupJava(osgunittest.OSGTestCase):

    def _select_old_alternative(self, config_type):
        java.select_ver(config_type, core.config['java.old-ver'][config_type])
        self.assert_(java.verify_ver(config_type, core.config['java.old-ver'][config_type]),
                     'could not select old java version %s' % core.config['java.old-ver'][config_type])

    def test_01_revert_java_ver(self):
        if java.is_openjdk_installed():
            self._select_old_alternative('java')

    def test_02_revert_javac_ver(self):
        if java.is_openjdk_devel_installed():
            self._select_old_alternative('javac')

