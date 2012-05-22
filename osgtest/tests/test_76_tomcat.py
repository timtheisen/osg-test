import glob
import os
import shutil
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.tomcat as tomcat

class TestStopTomcat(unittest.TestCase):

    def test_01_stop_tomcat(self):
        if not core.rpm_is_installed(tomcat.pkgname()):
            core.skip('not installed')
            return
        service.stop('tomcat')

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
        if core.missing_rpm(tomcat.pkgname(), 'emi-trustmanager-tomcat'):
            return
        files.restore(os.path.join(tomcat.sysconfdir(), 'server.xml'), 'tomcat')

    def test_04_remove_trustmanager(self):
        if core.missing_rpm(tomcat.pkgname(), 'emi-trustmanager-tomcat'):
            return

        # mv -f /etc/tomcat5/server.xml.old-trustmanager /etc/tomcat5/server.xml
        old_tm = os.path.join(tomcat.sysconfdir(), 'server.xml.old-trustmanager')
        new_tm = os.path.join(tomcat.sysconfdir(), 'server.xml')
        if os.path.exists(old_tm) and os.path.isdir(os.path.dirname(new_tm)):
            shutil.move(old_tm, new_tm)

        # rm -f /usr/share/tomcat5/server/lib/bcprov*.jar
        files.remove(os.path.join(tomcat.serverlibdir(), 'bcprov*.jar'))

        # rm -f /usr/share/tomcat5/server/lib/log4j*.jar
        files.remove(os.path.join(tomcat.serverlibdir(), 'log4j*.jar'))

        # rm -f /usr/share/tomcat5/server/lib/trustmanager-*.jar
        files.remove(os.path.join(tomcat.serverlibdir(), 'trustmanager-*.jar'))

        # rm -f /etc/tomcat5/log4j-trustmanager.properties
        files.remove(os.path.join(tomcat.sysconfdir(), 'log4j-trustmanager.properties'))

        # rm -f /var/lib/trustmanager-tomcat/server.xml
        files.remove('/var/lib/trustmanager-tomcat/server.xml')

        core.log_message('EMI trustmanager removed')
    
    def test_05_deconfig_tomcat(self):
        if core.missing_rpm(tomcat.pkgname()):
            return

        files.restore(tomcat.conffile(), 'tomcat')

