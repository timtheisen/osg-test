import glob
import os
import re
import shutil
import tempfile
import unittest

import osgtest.library.core as core

class TestFetchCrl(unittest.TestCase):

    error_message_whitelists = {
        '2': (
        ),
        '3': (
            'CRL has lastUpdate time in the future',
            'CRL has nextUpdate time in the past',
            'CRL verification failed for',
            'Download error'
        )
    }

    def output_is_acceptable(self, fetch_crl_output):
        whitelist = TestFetchCrl.error_message_whitelists[core.config['fetch-crl.major-version']]
        all_lines_ok = True
        for line in fetch_crl_output.rstrip('\n').split('\n'):
            line_ok = False
            for error_string in whitelist:
                if error_string in line:
                    line_ok = True
                    break
            if not line_ok:
                all_lines_ok = False
                break
        return all_lines_ok

    def test_01_determine_package_name(self):
        core.config['fetch-crl.package'] = None
        core.config['fetch-crl.version'] = None
        core.config['fetch-crl.major-version'] = None

        if core.rpm_is_installed('fetch-crl3'):
            core.config['fetch-crl.package'] = 'fetch-crl3'
        elif core.rpm_is_installed('fetch-crl'):
            core.config['fetch-crl.package'] = 'fetch-crl'
        else:
            return

        command = ('rpm', '--query', core.config['fetch-crl.package'])
        stdout = core.check_system(command, 'Get fetch-crl package NVR')[0]
        matches = re.match(r'fetch-crl[^-]*-(([^-])[^-]*)-[^-]+', stdout)
        self.assert_(matches is not None, 'Get %s NVR' % core.config['fetch-crl.package'])
        core.config['fetch-crl.version'] = matches.group(1)
        core.config['fetch-crl.major-version'] = matches.group(2)

    def test_02_fetch_crl(self):
        if core.config['fetch-crl.package'] is None:
            core.skip('Fetch CRL is not installed')
            return
        if not core.dependency_is_installed('grid-certificates'):
            core.skip('No certificates installed')
            return
        command = [core.config['fetch-crl.package']]
        status, stdout, stderr = core.system(command)
        fail = core.diagnose('Run %s in /etc' % core.config['fetch-crl.package'], status, stdout, stderr)
        if status == 1:
            self.assert_(self.output_is_acceptable(stdout), fail)
        else:
            self.assertEquals(status, 0, fail)
        count = len(glob.glob(os.path.join('/etc/grid-security/certificates', '*.r[0-9]')))
        self.assert_(count > 3, True)

    def test_03_fetch_crl_dir(self):
        if core.config['fetch-crl.package'] is None:
            core.skip('Fetch CRL is not installed')
            return
        if not core.dependency_is_installed('grid-certificates'):
            core.skip('No certificates installed')
            return
        temp_crl_dir = tempfile.mkdtemp()
        command = (core.config['fetch-crl.package'], '-o', temp_crl_dir)
        status, stdout, stderr = core.system(command)
        fail = core.diagnose('Run %s in temp dir' % core.config['fetch-crl.package'], status, stdout, stderr)
        if status == 1:
            self.assert_(self.output_is_acceptable(stdout), fail)
        else:
            self.assertEquals(status, 0, fail)
        count = len(glob.glob(os.path.join(temp_crl_dir, '*.r[0-9]')))
        shutil.rmtree(temp_crl_dir)
        self.assert_(count > 3, True)
