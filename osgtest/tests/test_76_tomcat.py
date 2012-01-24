import glob
import os
import osgtest.library.core as core
import shutil
import unittest

class TestStopTomcat(unittest.TestCase):

    def test_01_stop_tomcat(self):
        if not core.rpm_is_installed('tomcat5'):
            core.skip('not installed')
            return
        if not core.state['tomcat.started-server']:
            core.skip('did not start server')
            return

        command = ('service', 'tomcat5', 'stop')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Stop Tomcat service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assertEqual(stdout.find('FAILED'), -1, fail)
        self.assert_(not os.path.exists(core.config['tomcat.pid-file']),
                     'Tomcat server PID file still exists')

    def test_02_remove_vo_webapp(self):
        if not core.rpm_is_installed('voms-admin-server'):
            core.skip('not installed')
            return
        if not core.state['voms.installed-vo-webapp']:
            core.skip('did not start webapp')
            return

        command = ('service', 'voms-admin', 'stop')
        status, stdout, stderr = core.syspipe(command)
        fail = core.diagnose('Stop VOMS Admin service', status, stdout, stderr)
        self.assertEqual(status, 0, fail)
        self.assert_(not os.path.exists(core.config['voms.vo-webapp']),
                     'VOMS Admin VO context file still exists')

    def test_03_deconfig_tomcat_properties(self):
        if core.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return
        server_xml_path = '/etc/tomcat5/server.xml'
        server_xml_backup = server_xml_path + '.osgtest.backup'
        shutil.move(server_xml_backup, server_xml_path)

    def test_04_remove_trustmanager(self):
        if core.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return

        # mv -f /etc/tomcat5/server.xml.old-trustmanager /etc/tomcat5/server.xml
        old_tm = '/etc/tomcat5/server.xml.old-trustmanager'
        new_tm = '/etc/tomcat5/server.xml'
        if os.path.exists(old_tm) and os.path.isdir(os.path.dirname(new_tm)):
            shutil.move(old_tm, new_tm)

        # rm -f /usr/share/tomcat5/server/lib/bcprov*.jar
        for jar in glob.glob('/usr/share/tomcat5/server/lib/bcprov*.jar'):
            os.remove(jar)

        # rm -f /usr/share/tomcat5/server/lib/log4j*.jar
        for jar in glob.glob('/usr/share/tomcat5/server/lib/log4j*.jar'):
            os.remove(jar)

        # rm -f /usr/share/tomcat5/server/lib/trustmanager-*.jar
        for j in glob.glob('/usr/share/tomcat5/server/lib/trustmanager-*.jar'):
            os.remove(j)

        # rm -f /etc/tomcat5/log4j-trustmanager.properties
        if os.path.exists('/etc/tomcat5/log4j-trustmanager.properties'):
            os.remove('/etc/tomcat5/log4j-trustmanager.properties')

        # rm -f /var/lib/trustmanager-tomcat/server.xml
        if os.path.exists('/var/lib/trustmanager-tomcat/server.xml'):
            os.remove('/var/lib/trustmanager-tomcat/server.xml')

        core.log_message('EMI trustmanager removed')
