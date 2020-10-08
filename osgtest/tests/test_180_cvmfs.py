import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

CVMFS_CONFIG = """CVMFS_REPOSITORIES="`echo $((echo oasis.opensciencegrid.org;echo cms.cern.ch;ls /cvmfs)|sort -u)|tr ' ' ,`"
CVMFS_QUOTA_LIMIT=10000
CVMFS_HTTP_PROXY="http://squid-cs-b240.chtc.wisc.edu:3128|http://squid-cs-2360.chtc.wisc.edu:3128|http://squid-wid.chtc.wisc.edu:3128;DIRECT"
"""


class TestStartCvmfs(osgunittest.OSGTestCase):

    def setup_fuse(self):
        fuse_conf_path = '/etc/fuse.conf'
        files.preserve(fuse_conf_path, 'cvmfs')
        try:
            contents = files.read(fuse_conf_path)
        except IOError:
            # Sometimes this file doesn't exist
            contents = []
        for line in contents:
            if "user_allow_other" in line:
                return
        contents.append("user_allow_other\n")
        files.write(fuse_conf_path, contents, owner='cvmfs', backup=False, chmod=0o644)

    def setup_automount(self):
        automount_conf_path = '/etc/auto.master'
        files.preserve(automount_conf_path, 'cvmfs')
        try:
            contents = files.read(automount_conf_path)
        except IOError:
            # Sometimes this file doesn't exist
            contents = []
        for line in contents:
            if "cvmfs" in line:
                return
        contents.append("/cvmfs /etc/auto.cvmfs\n")
        files.write(automount_conf_path, contents, owner='cvmfs', backup=False, chmod=0o644)

    def setup_cvmfs(self):
        command = ('mkdir', '-p', '/tmp/cvmfs')
        status, stdout, stderr = core.system(command, False)
        files.write("/etc/cvmfs/default.local", CVMFS_CONFIG, owner='cvmfs', chmod=0o644)

        # Write verbose debug log for the OASIS repo
        oasis_repo = "oasis.opensciencegrid.org"
        files.write("/etc/cvmfs/config.d/%s.local" % oasis_repo,
                    "CVMFS_DEBUGLOG=/tmp/cvmfs/%s.log" % oasis_repo,
                    owner='cvmfs', chmod=0o644)

    def test_01_setup_cvmfs(self):
        core.skip_ok_unless_installed('cvmfs')

        self.setup_fuse()
        self.setup_automount()
        self.setup_cvmfs()

    def test_02_start_cvmfs(self):
        core.state['cvmfs.started-server'] = False

        core.skip_ok_unless_installed('cvmfs')

        stdout, stderr, fail = core.check_system(('service', 'autofs', 'restart'), 'Start cvmfs server')
        self.assert_(stdout.find('FAILED') == -1, fail)
        core.state['cvmfs.started-server'] = True
