import re

import osgtest.library.yum as yum
import osgtest.library.core as core
import osgtest.library.java as java
import osgtest.library.files as files
import osgtest.library.tomcat as tomcat
import osgtest.library.osgunittest as osgunittest

class TestJava(osgunittest.OSGTestCase):
    """
    This module implements sections 5.1.2 - 5.1.5 of
    https://twiki.opensciencegrid.org/bin/view/Documentation/Release3/InstallSoftwareWithOpenJDK7

    We avoid using skips in this module to limit their number in the results
    """

    def _select_alternatives(self, config_type):
        core.state['java.%s-selected' % config_type] = False
        if not java.is_openjdk_installed():
            return
        core.config['java.old-%s-ver' % config_type] = java.get_ver(config_type)

        if core.config['java.old-%s-ver' % config_type] != java.EXPECTED_VERSION:
            java.select_ver(config_type, java.EXPECTED_VERSION)
            self.assert_(java.verify_ver(config_type, java.EXPECTED_VERSION), 'incorrect java version selected')
            core.state['java.%s-selected' % config_type] = True

    def test_01_fix_symlinks(self):
        if core.rpm_is_installed('jdk') and java.is_openjdk_installed():
            core.config['java.bad_links'] = ['/usr/bin/java', '/usr/bin/javac', '/usr/bin/javadoc', '/usr/bin/jar']
            for link in core.config['java.bad_links']:
                files.preserve(link, owner='java')
            command = ('yum', 'reinstall', '-y', java.JAVA_RPM, java.JAVAC_RPM)
            yum.retry_command(command)

    def test_02_select_java_ver(self):
        self._select_alternatives('java')

    def test_03_select_javac_ver(self):
        self._select_alternatives('javac')

    def test_04_fix_tomcat_env(self):
        if core.rpm_is_installed(tomcat.pkgname()) and java.is_openjdk_installed():
            files.replace_regexpr('/etc/sysconfig/' + tomcat.pkgname(),
                                  r'^JAVA_HOME=',
                                  'JAVA_HOME="/etc/alternatives/jre"',
                                  owner='java')

    def test_05_fix_bestman_env(self):
        if core.rpm_regexp_is_installed(r'^bestman2') and java.is_openjdk_installed():
            files.replace_regexpr('/etc/sysconfig/bestman2',
                                  r'^JAVA_HOME=',
                                  'JAVA_HOME="/etc/alternatives/jre"',
                                  owner='java')

