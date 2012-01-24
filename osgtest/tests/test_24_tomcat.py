import os
import osgtest.library.core as core
import re
import shutil
import unittest

class TestStartTomcat(unittest.TestCase):

    def test_01_config_trustmanager(self):
        if core.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return

        command = ('/var/lib/trustmanager-tomcat/configure.sh',)
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Config trustmanager', status, stdout, stderr)
        self.assertEqual(status, 0, fail)

    def test_02_config_tomcat_properties(self):
        if core.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return

        server_xml_path = '/etc/tomcat5/server.xml'
        server_xml_backup = server_xml_path + '.osgtest.backup'
        shutil.move(server_xml_path, server_xml_backup)

        source_file = open(server_xml_backup, 'r')
        contents = source_file.read()
        source_file.close()

        new_contents = re.sub(r'crlRequired=".*?"', 'crlRequired="false"',
                              contents, re.IGNORECASE)

        target_file = open(server_xml_path, 'w')
        target_file.write(new_contents)
        target_file.close()

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
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Start Tomcat service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(os.path.exists(core.config['tomcat.pid-file']),
                     'Tomcat server PID file is missing')
        core.state['tomcat.started-server'] = True
