#pylint: disable=C0301
#pylint: disable=C0111
#pylint: disable=R0201
#pylint: disable=R0904
import os
import errno

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

class TestConfigureJobs(osgunittest.OSGTestCase):
    """Configurations for running jobs"""

    def test_01_set_job_env(self):
        # Jobs get submitted with globus-job-run, condor_run, and condor_ce_run
        core.state['jobs.env-set'] = False
        core.skip_ok_unless_one_installed(['htcondor-ce', 'globus-gatekeeper', 'condor'])

        osg_libdir = os.path.join('/var', 'lib', 'osg')
        try:
            os.makedirs(osg_libdir)
        except OSError, exc:
            if exc.errno != errno.EEXIST:
                raise
        core.config['osg.job-environment'] = os.path.join(osg_libdir, 'osg-job-environment.conf')
        core.config['osg.local-job-environment'] = os.path.join(osg_libdir, 'osg-local-job-environment.conf')

        files.write(core.config['osg.job-environment'],
                    "#!/bin/sh\nJOB_ENV='vdt'\nexport JOB_ENV",
                    owner='pbs', chmod=0644)
        files.write(core.config['osg.local-job-environment'],
                    "#!/bin/sh\nLOCAL_JOB_ENV='osg'\nexport LOCAL_JOB_ENV",
                    owner='pbs', chmod=0644)

        core.state['jobs.env-set'] = True

