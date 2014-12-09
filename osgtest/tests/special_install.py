import re
import time

import osgtest.library.core as core
import osgtest.library.yum as yum
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestInstall(osgunittest.OSGTestCase):

    def test_01_yum_repositories(self):
        pre = ('rpm', '--verify', '--nomd5', '--nosize', '--nomtime')
        core.check_system(pre + ('epel-release',), 'Verify epel-release')
        # If osg-release isn't installed, try osg-release-itb
        try:
            core.check_system(pre + ('osg-release',), 'Verify osg-release')
        except AssertionError:
            core.check_system(pre + ('osg-release-itb',), 'Verify osg-release + osg-release-itb')

    def test_02_disable_osg_release(self):
        # Disable osg-release on EL7 since we don't have any releases out yet
        # This can be removed when we do release something
        self.skip_ok_unless(core.el_release() == 7, 'Non-EL7 release')
        core.config['install.osg-repo-path'] = '/etc/yum.repos.d/osg.repo'
        files.replace(core.config['install.osg-repo-path'],
                      'enabled=1',
                      'enabled=0',
                      owner='install')
        
    def test_03_install_packages(self):
        core.state['install.success'] = False
        core.state['install.installed'] = []
        core.state['install.updated'] = []
        core.state['install.orphaned'] = []
        core.state['install.os_updates'] = []
        # Setting this so we can gracefully downgrade xrootd4 in the cleanup phase
        core.state['install.xrootd-replaced'] = False

        # Install packages
        core.state['install.transaction_ids'] = []
        fail_msg = ''
        deadline = time.time() + 3600   # 1 hour from now
        for package in core.options.packages:

            # Do not try to re-install packages
            if core.rpm_is_installed(package):
                continue

            # Attempt installation
            command = ['yum', '-y']
            for repo in core.options.extrarepos:
                command.append('--enablerepo=%s' % repo)
            command += ['install', package]

            retry_fail, status, stdout, stderr = yum.retry_command(command, deadline)
            if retry_fail == '':
            # This means retry the command succeeded
                if core.el_release() >= 6:
                    # RHEL 6 does not have the rollback option, so store the
                    # transaction IDs so we can undo each transaction in the
                    # proper order
                    core.state['install.transaction_ids'].append(yum.get_transaction_id())
                command = ('rpm', '--verify', package)
                core.check_system(command, 'Verify %s' % (package))
                yum.parse_output_for_packages(stdout)

            fail_msg += retry_fail
                
        if fail_msg:
            self.fail(fail_msg)
        core.state['install.success'] = True

    def test_04_update_osg_release(self):
        if not (core.options.updaterelease):
            return

        core.state['install.release-updated'] = False
        self.skip_bad_unless(core.state['install.success'], 'Install did not succeed')

        core.config['install.original-release-ver'] = core.osg_release(self)

        command = ['rpm', '-e', 'osg-release']
        core.check_system(command, 'Erase osg-release')
        
        self.assert_(re.match('\d+\.\d+', core.options.updaterelease), "Unrecognized updaterelease format")
        rpm_url = 'http://repo.grid.iu.edu/osg/' + core.options.updaterelease + '/osg-' + core.options.updaterelease \
            + '-el' + str(core.el_release()) + '-release-latest.rpm'
        command = ['rpm', '-Uvh', rpm_url]
        core.check_system(command, 'Update osg-release')
        
        # If update repos weren't specified, just use osg-release
        if not core.options.updaterepos:
            core.options.updaterepos = ['osg']

        core.state['install.release-updated'] = True
        
    def test_05_update_packages(self):
        if not (core.options.updaterepos and core.state['install.installed']):
            return
        
        self.skip_bad_unless(core.state['install.success'], 'Install did not succeed')

        # Update packages
        deadline = time.time() + 3600   # 1 hour from now

        command = ['yum', 'update', '-y']
        for repo in core.options.updaterepos:
            command.append('--enablerepo=%s' % repo)
        fail_msg, status, stdout, stderr = yum.retry_command(command, deadline)
        yum.parse_output_for_packages(stdout)

        if fail_msg:
            self.fail(fail_msg)
        else:
            if core.el_release() >=6:
                core.state['install.transaction_ids'].append(yum.get_transaction_id())

    def test_06_fix_java_symlinks(self):
        # This implements Section 5.1.2 of
        # https://twiki.opensciencegrid.org/bin/view/Documentation/Release3/InstallSoftwareWithOpenJDK7
        java7 = 'java-1.7.0-openjdk'
        java7_devel = 'java-1.7.0-openjdk-devel'

        # We don't use skip_ok_unless_installed because we want to limit the number of ok skips
        jdk_installed = False
        command = ('rpm', '--query', 'jdk')
        _, stdout, _ = core.system(command)
        if re.search("^jdk-1\.6\.\d+_\d+.*", stdout):
            jdk_installed = True

        if (jdk_installed and core.rpm_is_installed(java7) and core.rpm_is_installed(java7_devel)):
            command = ('rm', '-f', '/usr/bin/java', '/usr/bin/javac', '/usr/bin/javadoc', '/usr/bin/jar')
            core.check_system(command, 'Remove old symlinks')

            command = ('yum', 'reinstall', '-y', java7, java7_devel)
            core.check_system(command, 'Reinstall java7')
        
