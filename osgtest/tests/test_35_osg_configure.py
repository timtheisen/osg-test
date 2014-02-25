import os, re, unittest, sys, cStringIO

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestOSGConfigure(osgunittest.OSGTestCase):

    required_rpms = ['osg-configure',
                     'osg-configure-tests']
    required_rpms_ce = required_rpms + ['osg-ce']

    pathname = os.path.realpath('/usr/share/osg-configure/tests')
    sys_path_saved = None

    def test_00_setup(self):
        "setup system library path"
        cls = self.__class__
        if cls.pathname not in sys.path:
            cls.sys_path_saved = list(sys.path)
            sys.path.insert(0, cls.pathname)

    def test_01_version(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        command = ('osg-configure', '--version')
        stdout = core.check_system(command, 'osg-configure version check')[0]
        self.assert_(re.search('osg-configure \d+\.\d+\.\d+', 
                               stdout,
                               re.IGNORECASE)
                     is not None)

    def __run_unit_tests(self, test_case):
      """
      Runs a test suite and returns any error messages or failures
      """
      test_suite = unittest.TestSuite()
      test_suite.addTests(unittest.makeSuite(test_case))
      output = cStringIO.StringIO()
      result = unittest.TextTestRunner(stream=output, verbosity=2).run(test_suite)
      core.log_message(output.getvalue())
      output.close()
      if not result.wasSuccessful():
          error_message = "Encountered problems while running osg_configure unit tests (%s):\n" % type(test_case).__name__
          if result.errors != []:
              error_message = "Encountered the following errors: \n"
              for error in result.errors:
                  error_message = "%s:\n %s\n" % (error[0], error[1])
          if result.failures != []:
              error_message = "Encountered the following failures: \n"
              for failure in result.failures:
                  error_message = "%s:\n %s\n" % (failure[0], failure[1])

          return error_message
      return None
    
    
    def test_02_cemon(self):
        core.skip_ok_unless_installed(*self.required_rpms_ce)

        self.skip_ok_if(core.osg_release(self) == '3.2', 'cemon not supported in OSG > 3.1')
        
        try:
            import test_cemon
            mesg = self.__run_unit_tests(test_cemon.TestCEMon)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import cemon unit test: " + str(e))

    def test_03_condor(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
          import test_condor
          mesg = self.__run_unit_tests(test_condor.TestCondor)
          if mesg is not None:
            self.fail(mesg)
        except ImportError, e:
          self.fail("Can't import condor unit test: " + str(e))

    def test_04_configfile(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_configfile
            mesg = self.__run_unit_tests(test_configfile.TestConfigFile)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import configfile unit test: " + str(e))

    def test_05_gip(self):
        core.skip_ok_unless_installed(*self.required_rpms_ce)
        try:
            import test_gip
            mesg = self.__run_unit_tests(test_gip.TestGip)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import gip unit test: " + str(e))

    def test_06_gratia(self):
        core.skip_ok_unless_installed(*self.required_rpms_ce)
        try:
            import test_gratia
            mesg = self.__run_unit_tests(test_gratia.TestGratia)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import gratia unit test: " + str(e))

    def test_07_local_settings(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_local_settings
            mesg = self.__run_unit_tests(test_local_settings.TestLocalSettings)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import local settings unit test: " + str(e))

    def test_08_lsf(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_lsf
            mesg = self.__run_unit_tests(test_lsf.TestLSF)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import lsf unit test: " + str(e))

    def test_09_managedfork(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_managedfork
            mesg = self.__run_unit_tests(test_managedfork.TestManagedFork)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import managed fork unit test: " + str(e))

    def test_10_misc(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_misc
            mesg = self.__run_unit_tests(test_misc.TestMisc)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import misc unit test: " + str(e))

    def test_11_monalisa(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_monalisa
            mesg = self.__run_unit_tests(test_monalisa.TestMonalisa)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import monalisa unit test: " + str(e))

    def test_12_network(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_network
            mesg = self.__run_unit_tests(test_network.TestNetwork)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import network unit test: " + str(e))

    def test_13_pbs(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_pbs
            mesg = self.__run_unit_tests(test_pbs.TestPBS)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import pbs unit test: " + str(e))

    def test_14_rsv(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        if core.missing_rpm('rsv-core'):
            return
        try:
            import test_rsv
            mesg = self.__run_unit_tests(test_rsv.TestRSV)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import rsv unit test: " + str(e))

    def test_15_sge(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_sge
            mesg = self.__run_unit_tests(test_sge.TestSGE)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import sge unit test: " + str(e))

    def test_16_siteattributes(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_siteattributes
            mesg = self.__run_unit_tests(test_siteattributes.TestSiteAttributes)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import site attributes unit test: " + str(e))

    def test_17_squid(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_squid
            mesg = self.__run_unit_tests(test_squid.TestSquid)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import squid unit test: " + str(e))

    def test_18_storage(self):
        core.skip_ok_unless_installed(*self.required_rpms_ce)
        try:
            import test_storage
            if not os.path.exists('/tmp/etc'):
                os.mkdir('/tmp/etc')
                os.chmod('/tmp/etc', 0777)
            mesg = self.__run_unit_tests(test_storage.TestStorage)
            if mesg is not None:
                self.fail(mesg)
            os.rmdir('/tmp/etc')
        except ImportError, e:
            self.fail("Can't import storage unit test: " + str(e))

    def test_19_utilities(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_utilities
            mesg = self.__run_unit_tests(test_utilities.TestUtilities)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
          self.fail("Can't import utilities unit test: " + str(e))

    def test_20_validation(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_validation
            mesg = self.__run_unit_tests(test_validation.TestValidation)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import validation unit test: " + str(e))

    def test_21_xml_utilities(self):
        core.skip_ok_unless_installed(*self.required_rpms)
        try:
            import test_xml_utilities
            mesg = self.__run_unit_tests(test_xml_utilities.TestXMLUtilities)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import xml_utilities unit test: " + str(e))

    def test_22_info_services(self):
        core.skip_ok_unless_installed(*self.required_rpms_ce)
        osg_configure_envra = core.get_package_envra('osg-configure')
        osg_configure_version = osg_configure_envra[2]
        try:
            if [int(x) for x in osg_configure_version.split('.')] < [1, 0, 51]:
                self.skip_ok("info_services unit test was added in osg-configure-1.0.51")
        except ValueError: # Couldn't parse the version.
            pass           # Ignore it, might as well try to run the tests.

        try:
            import test_info_services
            mesg = self.__run_unit_tests(test_info_services.TestInfoServices)
            if mesg is not None:
                self.fail(mesg)
        except ImportError, e:
            self.fail("Can't import info_services unit test: " + str(e))

    def test_99_teardown(self):
        "restore system library path"
        cls = self.__class__
        if cls.sys_path_saved:
            sys.path = list(cls.sys_path_saved)

