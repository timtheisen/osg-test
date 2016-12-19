import os
import re

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.tomcat as tomcat
import osgtest.library.osgunittest as osgunittest

class TestStartTomcat(osgunittest.OSGTestCase):

    def test_01_config_trustmanager(self):
        core.skip_ok_unless_installed(tomcat.pkgname(), 'emi-trustmanager-tomcat')

        command = ('/var/lib/trustmanager-tomcat/configure.sh',)
        core.check_system(command, 'Config trustmanager')

    def test_02_config_tomcat_properties(self):
        if core.missing_rpm(tomcat.pkgname(), 'emi-trustmanager-tomcat'):
            return

        server_xml_path = os.path.join(tomcat.sysconfdir(), 'server.xml')
        old_contents = files.read(server_xml_path, True)
        pattern = re.compile(r'crlRequired=".*?"', re.IGNORECASE)
        new_contents = pattern.sub('crlRequired="false"', old_contents)
        files.write(server_xml_path, new_contents, owner='tomcat')

    def test_03_config_tomcat(self):
        core.skip_ok_unless_installed(tomcat.pkgname())

        old_contents = files.read(tomcat.conffile(), True)
        # Endorse JARs
        lines = ['JAVA_ENDORSED_DIRS="${JAVA_ENDORSED_DIRS+$JAVA_ENDORSED_DIRS:}/usr/share/voms-admin/endorsed"']
        # Improve Tomcat 7 startup times (SOFTWARE-2383)
        lines.append('JAVA_OPTS="-Djava.security.egd=file:/dev/./urandom"')

        for line in lines:
            if old_contents.find(line) != -1:
                lines.remove(line)

        new_contents = '\n'.join([old_contents] + lines)
        files.write(tomcat.conffile(), new_contents, owner='tomcat')

    def test_04_disable_persistence(self):
        core.skip_ok_unless_installed(tomcat.pkgname())
        self.skip_ok_if(core.options.nightly, 'Allow persistence in the nightlies')
        if core.el_release() > 5:
            # Disabling persistence doesn't appear to work on EL5
            # https://tomcat.apache.org/tomcat-5.5-doc/config/manager.html#Disable_Session_Persistence
            contents='''
<Context>
    <WatchedResource>WEB-INF/web.xml</WatchedResource>
    <Manager pathname="" />
</Context>
'''
            files.write(tomcat.contextfile(), contents, owner='tomcat')

    def test_04_configure_gratia(self):
        core.skip_ok_unless_installed(tomcat.pkgname(), 'gratia-service')
        command = ('/usr/share/gratia/configure_tomcat',)
        core.check_system(command, 'Unable to configure Gratia.')

    def test_05_start_tomcat(self):
        core.skip_ok_unless_installed(tomcat.pkgname())
        core.state['tomcat.started'] = False
        catalina_log = tomcat.catalinafile()

        initial_stat = core.get_stat(catalina_log)

        if tomcat.majorver() > 5:
            tomcat_sentinel = r'Server startup in \d+ ms'
            # tomcat5 doesn't have an explicit sentinel for server startup
            # so we use a heartbeat-like message that shows up in catalin.out
            # with an increased log level
            log_level = 'FINER'
        else:
            tomcat_sentinel = r'Start expire sessions'
            log_level = 'FINEST'

        # Bump log level
        core.config['tomcat.logging-conf'] = os.path.join(tomcat.sysconfdir(), 'logging.properties')
        files.append(core.config['tomcat.logging-conf'], 'org.apache.catalina.level = %s\n' % log_level,
                     owner='tomcat', backup=True)

        old_str  =  "1catalina.org.apache.juli.FileHandler.prefix = catalina."
        repl_str = ("1catalina.org.apache.juli.FileHandler.prefix = catalina\n"
                    "1catalina.org.apache.juli.FileHandler.rotatable = false")
        files.replace(core.config['tomcat.logging-conf'], old_str, repl_str,
                      owner='tomcat', backup=False)

        service.check_start(tomcat.pkgname())
        if core.options.nightly:
            timeout = 3600.0
        else:
            timeout = 1200.0
        line, gap = core.monitor_file(catalina_log, initial_stat, tomcat_sentinel, timeout)
        self.assert_(line is not None, 'Tomcat did not start within the %d min window' % int(timeout/60))
        core.state['tomcat.started'] = True
        core.log_message('Tomcat started after %.1f seconds' % gap)
