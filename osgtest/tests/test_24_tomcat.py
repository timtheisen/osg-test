import os
import re
import shutil
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.tomcat as tomcat

class TestStartTomcat(unittest.TestCase):

    def test_01_config_trustmanager(self):
        if core.missing_rpm(tomcat.pkgname(), 'emi-trustmanager-tomcat'):
            return

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

    def test_03_record_vomsadmin_start(self):
        core.state['voms.webapp-log-stat'] = None
        if core.missing_rpm(tomcat.pkgname(), 'voms-admin-server'):
            return
        if os.path.exists(core.config['voms.webapp-log']):
            core.state['voms.webapp-log-stat'] = \
                os.stat(core.config['voms.webapp-log'])

    def test_04_config_tomcat_endorsed_jars(self):
        if core.missing_rpm(tomcat.pkgname()):
            return

        old_contents = files.read(tomcat.conffile(), True)
        line = 'JAVA_ENDORSED_DIRS="${JAVA_ENDORSED_DIRS+$JAVA_ENDORSED_DIRS:}/usr/share/voms-admin/endorsed"\n'
        if old_contents.find(line) == -1:
            new_contents = old_contents + "\n" + line
            files.write(tomcat.conffile(), new_contents, owner='tomcat')

    def test_05_start_tomcat(self):
        if not core.rpm_is_installed(tomcat.pkgname()):
            core.skip('not installed')
            return
        
        service.start('tomcat', init_script=tomcat.pkgname(), sentinel_file=tomcat.pidfile())

