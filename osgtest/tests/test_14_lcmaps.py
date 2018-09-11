import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestLcMaps(osgunittest.OSGTestCase):

    required_rpms = ['lcmaps', 'lcmaps-db-templates', 'vo-client', 'vo-client-lcmaps-voms']

    def test_01_configure(self):
        core.config['lcmaps.db'] = '/etc/lcmaps.db'
        core.config['lcmaps.gsi-authz'] = '/etc/grid-security/gsi-authz.conf'

        core.skip_ok_unless_installed(*self.required_rpms)

        template = files.read('/usr/share/lcmaps/templates/lcmaps.db.vomsmap',
                              as_single_string=True)

        files.write(core.config['lcmaps.db'], template, owner='lcmaps')
        files.write(core.config['lcmaps.gsi-authz'],
                    "globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout\n",
                    owner='lcmaps')

    def test_02_xrootd_policy(self):
        core.skip_ok_unless_installed('xrootd-lcmaps', *self.required_rpms)
        self.skip_ok_unless(core.package_version_compare('xrootd-lcmaps', '1.4.0') >= 0)

        files.append(core.config['lcmaps.db'],
                     '''xrootd_policy:
verifyproxynokey -> banfile
banfile -> banvomsfile | bad
banvomsfile -> gridmapfile | bad
gridmapfile -> good | vomsmapfile
vomsmapfile -> good | defaultmapfile
defaultmapfile -> good | bad
''',
                     backup=False)
