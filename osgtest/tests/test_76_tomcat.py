import glob
import os
import osgtest.library.core as core
import osgtest.library.files as files
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
        stdout, stderr, fail = core.check_system(command, 'Stop Tomcat')
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
        core.check_system(command, 'Uninstall VOMS Admin webapp(s)')
        self.assert_(not os.path.exists(core.config['voms.vo-webapp']),
                     'VOMS Admin VO context file still exists')

    def test_03_deconfig_tomcat_properties(self):
        if core.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return
        files.restore('/etc/tomcat5/server.xml')

    def test_04_remove_trustmanager(self):
        if core.missing_rpm('tomcat5', 'emi-trustmanager-tomcat'):
            return

        # mv -f /etc/tomcat5/server.xml.old-trustmanager /etc/tomcat5/server.xml
        old_tm = '/etc/tomcat5/server.xml.old-trustmanager'
        new_tm = '/etc/tomcat5/server.xml'
        if os.path.exists(old_tm) and os.path.isdir(os.path.dirname(new_tm)):
            shutil.move(old_tm, new_tm)

        # rm -f /usr/share/tomcat5/server/lib/bcprov*.jar
        files.remove('/usr/share/tomcat5/server/lib/bcprov*.jar')

        # rm -f /usr/share/tomcat5/server/lib/log4j*.jar
        files.remove('/usr/share/tomcat5/server/lib/log4j*.jar')

        # rm -f /usr/share/tomcat5/server/lib/trustmanager-*.jar
        files.remove('/usr/share/tomcat5/server/lib/trustmanager-*.jar')

        # rm -f /etc/tomcat5/log4j-trustmanager.properties
        files.remove('/etc/tomcat5/log4j-trustmanager.properties')

        # rm -f /var/lib/trustmanager-tomcat/server.xml
        files.remove('/var/lib/trustmanager-tomcat/server.xml')

        core.log_message('EMI trustmanager removed')
