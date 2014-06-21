import os
import pwd
import unittest

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.certificates as certs

class TestOSGInfoServices(osgunittest.OSGTestCase):
    
    possible_rpms = ['osg-ce',
                     'htcondor-ce']
    def test_01_osg_configure_v(self):
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        command = ('osg-configure', '-v')
        core.check_system(command, 'osg-configure -v')

    def test_02_osg_configure_c(self):
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        command = ('osg-configure', '-c')
        core.check_system(command, 'osg-configure -c')

    def test_03_osg_info_services(self):
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        command = ('osg-info-services', '--dryrun')
        core.check_system(command,'osg-info-services dry run')

