import cagen
import re
import os

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.condor as condor

class TestStartCondorCE(osgunittest.OSGTestCase):
    # Tests 01-02 are needed to reconfigure condor to work with HTCondor-CE
    def test_01_write_condor_config(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client')

        core.config['condor-ce.condor-cfg'] = '/etc/condor/config.d/99-osgtest.condor.conf'
        contents = """SCHEDD_INTERVAL=5"""

        files.write(core.config['condor-ce.condor-cfg'],
                    contents,
                    owner='condor-ce',
                    chmod=0644)

    def test_02_reconfigure_condor(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client')
        self.skip_bad_unless(core.state['condor.running-service'], 'Condor not running')

        command = ('condor_reconfig', '-debug')
        core.check_system(command, 'Reconfigure Condor')
        self.assert_(condor.is_running(),
                     'Condor not running after reconfig')

    def test_03_configure_authentication(self):
        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client')

        # Configure condor-ce to use the gridmap file and set up PBS and Condor routes
        core.config['condor-ce.condor-ce-cfg'] = '/etc/condor-ce/config.d/99-osgtest.condor-ce.conf'
        condor_contents = """GRIDMAP = /etc/grid-security/grid-mapfile
ALL_DEBUG=D_FULLDEBUG
JOB_ROUTER_ENTRIES = \\
   [ \\
     GridResource = "batch pbs"; \\
     TargetUniverse = 9; \\
     name = "Local_PBS"; \\
     Requirements = target.osgTestPBS =?= true; \\
   ] \\
   [ \\
     TargetUniverse = 5; \\
     name = "Local_Condor"; \\
   ]

JOB_ROUTER_SCHEDD2_SPOOL=/var/lib/condor/spool
JOB_ROUTER_SCHEDD2_NAME=$(FULL_HOSTNAME)
JOB_ROUTER_SCHEDD2_POOL=$(FULL_HOSTNAME):9618
"""
        files.write(core.config['condor-ce.condor-ce-cfg'],
                    condor_contents,
                    owner='condor-ce',
                    chmod=0644)

        # lcmaps needs to know to use the gridmap file instead of GUMS
        core.config['condor-ce.lcmapsdb'] = '/etc/lcmaps.db'
        lcmaps_contents = """
authorize_only:
gridmapfile -> good | bad
"""
        files.append(core.config['condor-ce.lcmapsdb'], lcmaps_contents, owner='condor-ce')

        # Add host DN to condor_mapfile
        if core.options.hostcert:
            core.config['condor-ce.condorce_mapfile'] = '/etc/condor-ce/condor_mapfile'
            hostcert_dn, _ = cagen.certificate_info(core.config['certs.hostcert'])
            mapfile_contents = files.read('/etc/condor-ce/condor_mapfile')
            mapfile_contents.insert(0, re.sub(r'([/=\.])', r'\\\1', "GSI \"^%s$\" " % hostcert_dn) + \
                                              "%s@daemon.opensciencegrid.org\n" % core.get_hostname())
            files.write(core.config['condor-ce.condorce_mapfile'],
                        mapfile_contents,
                        owner='condor-ce',
                        chmod=0644)

    def test_05_start_condorce(self):
        core.config['condor-ce.lockfile'] = '/var/lock/subsys/condor-ce'
        core.state['condor-ce.started'] = False

        core.skip_ok_unless_installed('condor', 'htcondor-ce', 'htcondor-ce-client')
        self.skip_ok_if(os.path.exists(core.config['condor-ce.lockfile']), 'already running')

        command = ('service', 'condor-ce', 'start')
        stdout, _, fail = core.check_system(command, 'Start HTCondor CE')
        self.assert_(stdout.find('FAILED') == -1, fail)
        self.assert_(os.path.exists(core.config['condor-ce.lockfile']),
                     'HTCondor CE run lock file missing')
        core.state['condor-ce.started'] = True
