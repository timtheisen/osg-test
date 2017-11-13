import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestLcMaps(osgunittest.OSGTestCase):

    def test_01_configure(self):
        core.config['lcmaps.db'] = '/etc/lcmaps.db'
        core.config['lcmaps.gsi-authz'] = '/etc/grid-security/gsi-authz.conf'

        core.skip_ok_unless_installed('lcmaps', 'lcmaps-db-templates')

        template = files.read('/usr/share/lcmaps/templates/lcmaps.db.vomsmap',
                              as_single_string=True)

        files.write(core.config['lcmaps.db'], template, owner='lcmaps')
        files.write(core.config['lcmaps.gsi-authz'],
                    "globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout\n",
                    owner='lcmaps')
