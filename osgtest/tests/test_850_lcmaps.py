import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestRestoreLcMaps(osgunittest.OSGTestCase):

    @core.osgrelease(3.5)
    def test_01_restore_lcmaps(self):
        core.skip_ok_unless_installed('lcmaps', 'lcmaps-plugins-voms', 'lcmaps-db-templates')

        files.restore(core.config['lcmaps.gsi-authz'], 'lcmaps')
        files.restore(core.config['lcmaps.db'], 'lcmaps')
