import os

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.tomcat as tomcat

class TestStopGratia(osgunittest.OSGTestCase):

    def setUp(self):
        self.skip_ok_if(core.el_release() > 6, "Do not run Gratia tests on EL7")

    #This test removes the http certificates, if not already removed earlier
    def test_01_remove_certs(self):

        core.skip_ok_unless_installed('gratia-service')
        if core.state['voms.removed-certs']:
            return
        # Do the keys first, so that the directories will be empty for the certs.
        core.remove_cert('certs.httpkey')
        core.remove_cert('certs.httpcert')

    #This test drops the gratia database
    def test_02_uninstall_gratia_database(self):
        core.skip_ok_unless_installed('gratia-service')

        filename = "/tmp/gratia_admin_pass." + str(os.getpid()) + ".txt"
        contents = "[client]\n" + "password=\n"
        files.write(filename, contents, backup=False)

        # Command to drop the gratia database is:
        # echo "drop database gratia;" | mysql --defaults-extra-file="/tmp/gratia_admin_pass.<pid>.txt" -B --unbuffered
        # --user=root --port=3306
        command = "echo \"drop database gratia_osgtest;\" | " + \
                  "mysql --defaults-extra-file=\"" + \
                  filename + \
                  "\" -B --unbuffered  --user=root --port=3306"
        core.check_system(command, 'Unable to drop Gratia Database.', shell=True)
        files.remove(filename)
        #At this time, remove the gratia reader password file also
        files.remove(core.config['gratia.sql.file'])

    #This test cleans up gridftp related files
    def test_03_cleanup_gridftp(self):

        core.skip_ok_unless_installed('gratia-probe-gridftp-transfer', 'gratia-service')
        try:
            files.remove("/var/log/gridftp.log")
            files.remove("/var/log/gridftp-auth.log")
            probeconfig = core.config['gratia.config.dir'] + "/gridftp-transfer/ProbeConfig"
            owner = os.path.basename(os.path.dirname(probeconfig))
            files.restore(probeconfig, owner)
        except OSError as e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise

    #This test cleans up glexec related files
    def test_04_cleanup_glexec(self):

        core.skip_ok_unless_installed('gratia-probe-glexec', 'gratia-service')
        try:
            files.remove("/var/log/glexec.log")
            files.remove("/var/lib/gratia/data/glexec_plugin.chk")
            probeconfig = core.config['gratia.config.dir'] + "/glexec/ProbeConfig"
            owner = os.path.basename(os.path.dirname(probeconfig))
            files.restore(probeconfig, owner)
        except OSError as e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise
        
    #This test cleans up condor related files
    def test_06_cleanup_condor(self):
        core.skip_ok_unless_installed('gratia-probe-condor', 'gratia-service')
        try:
            probeconfig = core.config['gratia.config.dir'] + "/condor/ProbeConfig"
            owner = os.path.basename(os.path.dirname(probeconfig))
            files.restore(probeconfig, owner)
        except OSError as e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise

    #This test cleans up pbs related files
    def test_07_cleanup_pbs(self):
        core.skip_ok_unless_installed('gratia-probe-pbs-lsf', 'gratia-service')
        try:
            files.remove("/var/spool/pbs/server_priv/accounting", True)
            probeconfig = core.config['gratia.config.dir'] + "/pbs-lsf/ProbeConfig"
            owner = os.path.basename(os.path.dirname(probeconfig))
            files.restore(probeconfig, owner)
        except OSError as e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise

    #This test cleans up sge related files
    def test_08_cleanup_sge(self):
        core.skip_ok_unless_installed('gratia-probe-sge', 'gratia-service')
        try:
            files.remove("/var/log/accounting", True)
            probeconfig = core.config['gratia.config.dir'] + "/sge/ProbeConfig"
            owner = os.path.basename(os.path.dirname(probeconfig))
            files.restore(probeconfig, owner)
        except OSError as e:
            if e.errno == 2:
                # suppress "No such file or directory" error
                pass
            else:
                # reraise the exception, as it's an unexpected error
                raise

    #This test restores the mentioned gratia directory, if it was backed up
    def test_09_restore_varlibgratia(self):
        core.skip_ok_unless_installed('gratia-service')
        if 'gratia.varlibgratia-backedup' in core.state:
            files.remove('/var/lib/gratia', True)
            command = ("mv /var/lib/gratia_production /var/lib/gratia",)
            core.check_system(command, 'Could not restore /var/lib/gratia', shell=True)

    #This test restores the mentioned gratia-service directory, if it was backed up
    def test_10_restore_varlibgratiaservice(self):
        core.skip_ok_unless_installed('gratia-service')
        if 'gratia.varlibgratia-service-backedup' in core.state:
            files.remove('/var/lib/gratia-service', True)
            command = ("mv /var/lib/gratia-service_production /var/lib/gratia-service",)
            core.check_system(command, 'Could not restore /var/lib/gratia-service', shell=True)

    #This test restores the mentioned gratia-service directory, if it was backed up 
    def test_11_restore_etcgratia_collector_or_services(self):
        core.skip_ok_unless_installed('gratia-service')
        if 'gratia.etcgratia_collector_or_services-backedup' in core.state:
            gratia_directory_to_preserve = core.state['gratia.etcgratia_collector_or_services-backedup']
            backup_path = gratia_directory_to_preserve + '_production'
            files.remove(gratia_directory_to_preserve, True)
            command = ("mv " + backup_path + " " + gratia_directory_to_preserve,)
            core.check_system(command, 'Could not restore ' + gratia_directory_to_preserve, shell=True)

    def test_12_restore_user_vo_map_file(self):
        core.skip_ok_unless_installed('gratia-service')
        if files.filesBackedup(core.config['gratia.user-vo-map'], 'root'):
            files.restore(core.config['gratia.user-vo-map'], 'root')

    def test_13_restore_tomcat_template(self):
        if core.el_release() == 7:
            core.skip_ok_unless_installed(tomcat.pkgname(), 'gratia-service')
            files.restore(core.config['gratia.broken_template'], 'gratia')
