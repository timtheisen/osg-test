import os
import osgtest.library.core as core
import osgtest.library.files as files
import re
import shutil
import unittest

class TestStartTomcat(unittest.TestCase):

    def test_01_config_trustmanager(self):
        if core.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return

        command = ('/var/lib/trustmanager-tomcat/configure.sh',)
        core.check_system(command, 'Config trustmanager')

    def test_02_config_tomcat_properties(self):
        if core.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return

        server_xml_path = '/etc/tomcat5/server.xml'
        old_contents = files.read(server_xml_path, True)
        pattern = re.compile(r'crlRequired=".*?"', re.IGNORECASE)
        new_contents = pattern.sub('crlRequired="false"', old_contents)
        files.write(server_xml_path, new_contents)

    def test_03_record_vomsadmin_start(self):
        core.state['voms.webapp-log-stat'] = None
        if core.missing_rpm('tomcat5', 'voms-admin-server'):
            return
        if os.path.exists(core.config['voms.webapp-log']):
            core.state['voms.webapp-log-stat'] = \
                os.stat(core.config['voms.webapp-log'])

    def test_04_start_tomcat(self):
        core.config['tomcat.pid-file'] = '/var/run/tomcat5.pid'
        core.state['tomcat.started-server'] = False

        if not core.rpm_is_installed('tomcat5'):
            core.skip('not installed')
            return
        if os.path.exists(core.config['tomcat.pid-file']):
            core.skip('apparently running')
            return

        command = ('service', 'tomcat5', 'start')
        stdout, stderr, fail = core.check_system(command, 'Start Tomcat')
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(os.path.exists(core.config['tomcat.pid-file']),
                     'Tomcat server PID file is missing')
        core.state['tomcat.started-server'] = True
