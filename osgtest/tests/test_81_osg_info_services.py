import glob
import os
import pwd
import re
import shutil
import socket
import time
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.certificates as certs

class TestStopOSGInfoServices(osgunittest.OSGTestCase):

    possible_rpms = ['osg-ce',
                     'htcondor-ce']
    
    def test_01_restore_basic_configFile(self):
        core.skip_ok_unless_installed('osg-info-services')
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        files.restore(core.config['osg-info-services.storage-file'], 'root')
        files.restore(core.config['osg-info-services.squid-file'], 'root')
        files.restore(core.config['osg-info-services.misc-file'], 'root')
        files.restore(core.config['osg-info-services.gip-file'], 'root')
        files.restore(core.config['osg-info-services.siteinfo-file'], 'root')
        files.restore(core.config['osg-info-services.gratia-file'], 'root')
        files.restore(core.config['osg-info-services.gateway-file'], 'root')

    def test_02_restore_condor_configFile(self):
        core.skip_ok_unless_installed(['osg-info-services', 'osg-ce-condor'])
        files.restore(core.config['osg-info-services.condor-file'], 'root')

    def test_03_restore_pbs_configFile(self):
        core.skip_ok_unless_installed(['osg-info-services', 'osg-ce-pbs'])
        files.restore(core.config['osg-info-services.pbs-file'], 'root')

    def test_04_restore_lsf_configFile(self):
        core.skip_ok_unless_installed(['osg-info-services', 'osg-ce-lsf'])
        files.restore(core.config['osg-info-services.lsf-file'], 'root')

    def test_05_restore_sge_configFile(self):
        core.skip_ok_unless_installed(['osg-info-services', 'osg-ce-sge'])
        files.restore(core.config['osg-info-services.sge-file'], 'root')

    def test_06_delete_temporary_appdir_structure(self):
        core.skip_ok_unless_installed('osg-info-services')
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        command = ('rm', '-rf',core.config['osg-info-services.tmp-dir-suffix'])
        core.check_system(command, 'remove temporary app_dir structure %s' % core.config['osg-info-services.tmp-dir-suffix'])
    
    def test_07_restore_user_vo_map_file(self):
        core.skip_ok_unless_installed('osg-info-services')
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        if files.filesBackedup(core.config['osg-info-services.user-vo-map'], 'root'):
            files.restore(core.config['osg-info-services.user-vo-map'], 'root')
        
