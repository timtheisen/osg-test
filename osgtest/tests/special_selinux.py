import re

import osgtest.library.core as core
import osgtest.library.osgunittest as osgunittest


class TestSelinux(osgunittest.OSGTestCase):
    def test_01_selinux(self):
        core.state['selinux.mode'] = None
        if not core.options.selinux:
            return

        self.skip_bad_unless(core.rpm_is_installed('policycoreutils') and
                             core.rpm_is_installed('libselinux-utils'),
                             'missing SELinux utils')

        stdout, _, _ = core.check_system(('sestatus',), 'acquire current selinux mode')
        try:
            core.state['selinux.mode'] = re.search(r'Current mode:\s*(\w*)', stdout, re.MULTILINE).group(1)
            if core.state['selinux.mode'] == 'permissive':
                core.check_system(('setenforce', 'Enforcing'), 'set selinux mode to enforcing')
        except AttributeError:
            # If 'Current mode' doesn't appear, SELinux is probably in disabled mode
            # and we cannot enable it via command-line utilities
            core.state['selinux.mode'] = ''
            self.fail("SELinux disabled: cannot enable SELinux from disabled mode")

