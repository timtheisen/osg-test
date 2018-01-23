import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStopGUMS(osgunittest.OSGTestCase):

    @core.osgrelease(3.3)
    def test_01_restore_files(self):
        core.skip_ok_unless_installed('gums-service')
        files.restore(core.config['gums.config-file'], 'gums')
