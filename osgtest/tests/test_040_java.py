import osgtest.library.yum as yum
import osgtest.library.core as core
import osgtest.library.java as java
import osgtest.library.osgunittest as osgunittest

class TestJava(osgunittest.OSGTestCase):
    """
    This module implements the java installation instructions for OSG:
    https://twiki.opensciencegrid.org/bin/view/Documentation/Release3/InstallSoftwareWithOpenJDK7

    We avoid using skips in this module to limit their number in the results
    """

    def _select_alternatives(self, config_type):
        core.config['java.old-ver'][config_type] = java.get_ver(config_type)
        java.select_ver(config_type, '%s-openjdk' % java.EXPECTED_VERSION)
        self.assert_(java.verify_ver(config_type, java.EXPECTED_VERSION), 'incorrect java version selected')

    def test_00_setup(self):
        if java.is_openjdk_installed() or java.is_openjdk_devel_installed():
            core.config['java.old-ver'] = {}

    def test_01_select_java_ver(self):
        if java.is_openjdk_installed():
            self._select_alternatives('java')

    def test_02_select_javac_ver(self):
        if java.is_openjdk_devel_installed():
            self._select_alternatives('javac')
