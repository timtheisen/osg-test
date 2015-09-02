#pylint: disable=C0301
#pylint: disable=C0111
#pylint: disable=R0201
#pylint: disable=R0904

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestCleanupJobs(osgunittest.OSGTestCase):
    """Clean any configuration we touched for running jobs"""

    def test_01_restore_job_env(self):
        core.skip_ok_unless_installed('osg-configure')
        core.skip_ok_unless_one_installed(['htcondor-ce', 'globus-gatekeeper', 'condor'])

        files.restore(core.config['osg.job-environment'], owner='pbs')
        files.restore(core.config['osg.local-job-environment'], owner='pbs')
