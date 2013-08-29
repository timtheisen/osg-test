import os
import shutil

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestStopGUMS(osgunittest.OSGTestCase):

    def test_01_remove_cert_dir(self):
        core.skip_ok_unless_installed('gums-service')

        self.skip_bad_unless(os.path.isdir(core.config['gums.certdir']), 'Missing .globus dir')
        files.remove(core.config['gums.certdir'], force=True)

        # Restore backup if one exists.
        try:
            shutil.move(core.config['gums.backup-certdir'], core.config['gums.certdir'])
        except IOError, e:
            if e.errno == 2:
                # suppress no such file or directory error
                pass
            else:
                raise
