import os
import time
from datetime import date

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest
import osgtest.library.service as service

class TestStartPBS(osgunittest.OSGTestCase):

    pbs_config = """
create queue batch queue_type=execution
set queue batch started=true
set queue batch enabled=true
set queue batch resources_default.nodes=1
set queue batch resources_default.walltime=3600
set server default_queue=batch
set server keep_completed = 600
set server job_nanny = True
set server scheduling=true
set server acl_hosts += *
set server acl_host_enable = True
"""
    required_rpms = ['torque-mom',
                     'torque-server',
                     'torque-scheduler',
                     'torque-client', # for qmgr
                     'munge']


    def test_01_start_munge(self):
        if core.el_release() == 5:
            core.config['munge.lockfile'] = '/var/lock/subsys/munge'
        elif core.el_release() == 6:
            core.config['munge.lockfile'] = '/var/lock/subsys/munged'
        elif core.el_release() == 7:
            core.config['munge.lockfile'] = '/var/run/munge/munged.pid'
        core.config['munge.keyfile'] = '/etc/munge/munge.key'
        core.state['munge.running'] = False

        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(service.is_running('munge'), 'already running')

        files.preserve(core.config['munge.keyfile'], 'pbs')
        command = ('/usr/sbin/create-munge-key', '-f',)
        stdout, _, fail = core.check_system(command, 'Create munge key')
        self.assert_(stdout.find('error') == -1, fail)

        service.start('munge')
        self.assert_(service.is_running('munge'), 'munge failed to start')
        core.state['munge.running'] = True

    def test_02_start_mom(self):
        if core.el_release() <= 6:
            core.config['torque.mom-lockfile'] = '/var/lock/subsys/pbs_mom'
        else:
            core.config['torque.mom-lockfile'] = '/var/lib/torque/mom_priv/mom.lock'
        core.state['torque.pbs-mom-running'] = False

        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(service.is_running('pbs_mom'), 'PBS mom already running')

        core.config['torque.mom-config'] = '/var/lib/torque/mom_priv/config'
        files.write(core.config['torque.mom-config'],
                    "$pbsserver %s\n" % core.get_hostname(),
                    owner='pbs')
        core.config['torque.mom-layout'] = '/var/lib/torque/mom_priv/mom.layout'
        files.write(core.config['torque.mom-layout'],
                    "nodes=0",
                    owner='pbs')

        service.start('pbs_mom')
        self.assert_(service.is_running('pbs_mom'), 'PBS mom failed to start')
        core.state['torque.pbs-mom-running'] = True


    def test_03_start_pbs_sched(self):
        if core.el_release() <= 6:
            core.config['torque.sched-lockfile'] = '/var/lock/subsys/pbs_sched'
        else:
            core.config['torque.sched-lockfile'] = '/var/lib/torque/sched_priv/sched.lock'
        core.state['torque.pbs-sched-running'] = False

        core.skip_ok_unless_installed(*self.required_rpms)
        self.skip_ok_if(service.is_running('pbs_sched'), 'PBS sched already running')

        service.start('pbs_sched')
        self.assert_(service.is_running('pbs_sched'), 'PBS sched failed to start')
        core.state['torque.pbs-sched-running'] = True

    def test_04_start_pbs(self):
        if core.el_release() <= 6:
            core.config['torque.pbs-lockfile'] = '/var/lock/subsys/pbs_server'
        else:
            core.config['torque.pbs-lockfile'] = '/var/lib/torque/server_priv/server.lock'
        core.state['trqauthd.started-service'] = False
        core.state['torque.pbs-server-running'] = False
        core.state['torque.pbs-server-started'] = False
        core.state['torque.pbs-configured'] = False
        core.state['torque.nodes-up'] = False
        core.config['torque.pbs-nodes-file'] = '/var/lib/torque/server_priv/nodes'
        core.config['torque.pbs-servername-file'] = '/var/lib/torque/server_name'

        core.skip_ok_unless_installed(*self.required_rpms)
        if os.path.exists(core.config['torque.pbs-lockfile']):
            core.state['torque.pbs-server-running'] = True
            self.skip_ok('pbs server apparently running')

        # set hostname as servername instead of localhost
        files.write(core.config['torque.pbs-servername-file'],
                    "%s" % core.get_hostname(),
                    owner='pbs')
        core.state['torque.pbs-configured'] = True

        # trqauthd is required for the pbs_server
        service.start('trqauthd')

        if not os.path.exists('/var/lib/torque/server_priv/serverdb'):
            if core.el_release() <= 6:
                command = 'service pbs_server create' # this creates the default config and starts the service
            else:
                # XXX: "service pbs_server create" doesn't work for systemd, and I haven't found a
                #      systemd equivalent to do the "create" step in el7 ... The following was
                #      distilled from the el6 init.d script:  (but please correct as necessary)
                command = ('/usr/sbin/pbs_server -d /var/lib/torque -t create -f && '
                           'sleep 10 && /usr/bin/qterm')

            stdout, _, fail = core.check_system(command, 'create initial pbs serverdb config', shell=True)
            self.assert_(stdout.find('error') == -1, fail)

        # This gets wiped if we write it before the initial 'service pbs_server create'
        # However, this file needs to be in place before the service is started so we
        # restart the service after 'initial configuration'
        files.write(core.config['torque.pbs-nodes-file'], # add the local node as a compute node
                    "%s np=1 num_node_boards=1\n" % core.get_hostname(),
                    owner='pbs')

        # Sometimes the restart command throws an error on stop but still manages
        # to kill the service, meaning that the service doesn't get brought back up
        service.stop('pbs_server')

        server_log = '/var/log/torque/server_logs/' + date.today().strftime('%Y%m%d')
        try:
            server_log_stat = os.stat(server_log)
        except OSError:
            server_log_stat = None


        service.start('pbs_server')
        self.assert_(service.is_running('pbs_server'), 'PBS server failed to start')
        core.state['torque.pbs-server-started'] = True
        core.state['torque.pbs-server-running'] = True

        # Wait until the server is up before writing the rest of the config
        core.monitor_file(server_log, server_log_stat, '.*Server Ready.*', 60.0)
        core.check_system("echo '%s' | qmgr %s" % (self.pbs_config, core.get_hostname()),
                          "Configuring pbs server",
                          shell=True)

        # wait up to 5 minutes for the server to recognize the node
        start_time = time.time()
        while (time.time() - start_time) < 600:
            command = ('/usr/bin/qnodes', '-s', core.get_hostname())
            stdout, _, fail = core.check_system(command, 'Get pbs node info')
            self.assert_(stdout.find('error') == -1, fail)
            if stdout.find('state = free'):
                core.state['torque.nodes-up'] = True
                break
        if not core.state['torque.nodes-up']:
            self.fail('PBS nodes not coming up')

