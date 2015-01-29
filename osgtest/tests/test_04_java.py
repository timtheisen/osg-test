import re

import osgtest.library.yum as yum
import osgtest.library.core as core
import osgtest.library.java as java
import osgtest.library.files as files
import osgtest.library.tomcat as tomcat
import osgtest.library.osgunittest as osgunittest

class TestJava(osgunittest.OSGTestCase):
    """
    This module implements the java installation instructions for OSG:
    https://twiki.opensciencegrid.org/bin/view/Documentation/Release3/InstallSoftwareWithOpenJDK7

    We avoid using skips in this module to limit their number in the results
    """

    def _select_alternatives(self, config_type):
        core.config['java.old-%s-ver' % config_type] = java.get_ver(config_type)
        java.select_ver(config_type, '%s-openjdk' % java.EXPECTED_VERSION)
        self.assert_(java.verify_ver(config_type, java.EXPECTED_VERSION), 'incorrect java version selected')

    def test_01_fix_symlinks(self):
        if core.rpm_is_installed('jdk') and \
           (java.is_openjdk_installed() or java.is_openjdk_devel_installed()):
            # We regenerate these symlinks via alternatives so it's unnecessary to back them up
            command = ('rm', '-f', '/usr/bin/java', '/usr/bin/javac', '/usr/bin/javadoc', '/usr/bin/jar')
            core.check_system(command, 'Remove old symlinks')
            command = ('yum', 'reinstall', '-y', java.JAVA_RPM, java.JAVAC_RPM)
            yum.retry_command(command)

    def test_02_select_java_ver(self):
        if not java.is_openjdk_installed():
            return
        self._select_alternatives('java')
        command = ('ls', '-l', '/etc/alternatives')
        core.check_system(command, 'check alternatives')

    def test_03_select_javac_ver(self):
        if not java.is_openjdk_devel_installed():
            return
        self._select_alternatives('javac')
