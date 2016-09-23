"""Utilities for starting and stopping init-based services."""
import os
import time

import osgtest.library.core as core

def _init_script_name(service_name, init_script=None):
    """Get the init script name, preferring the values in this order:
    1. Predefined global
    2. Explicity defined init script name
    3. Service name
    """
    if init_script is None:
        init_script = service_name
    init_script = core.config.get(service_name + '.init-script', init_script)
    core.config[service_name + '.init-script'] = init_script
    return init_script

def start(service_name, init_script=None, sentinel_file=None):
    """Start a service via init script or systemd.

    'service_name' is used as the base of the keys in the core.config and
    core.state dictionaries. It is also used as the value of 'init_script',
    if it is not specified.

    The service is started by doing "service init_script start" or "systemctl
    start service_name".

    'sentinel_file' is the path to a pid file or lock file, or some other file
    that is expected to exist iff the service is running.

    The service is not started up if the sentinel file exists, or if
    core.state[service_name.started-service] is True.

    The following globals are set:
    core.config[service_name.init-script] is set to the value of init_script
    (or service_name if not specified).
    core.state[service_name.started-service] is set to True on successful
    startup, False otherwise.
    core.config[service_name.sentinel-file] is set to the value of sentinel_file,
    if specified.

    """
    init_script = _init_script_name(service_name, init_script)

    if sentinel_file and os.path.exists(sentinel_file):
        core.skip('service ' + service_name + ' already running (sentinel file found)')
        return
    if core.state.get(service_name + '.started-service'):
        core.skip('service ' + service_name + ' already running (flagged as started)')
        return

    if core.el_release() >= 7:
        command = ('systemctl', 'start', init_script)
    else:
        command = ('service', init_script, 'start')
    core.check_system(command, 'Start ' + service_name + ' service')

    if sentinel_file:
        assert os.path.exists(sentinel_file), "%(service_name)s sentinel file not found at %(sentinel_file)s" % locals()
        core.config[service_name + '.sentinel-file'] = sentinel_file

    core.state[service_name + '.started-service'] = True


def stop(service_name):
    """Stop a service via init script or systemd.

    'service_name' is used as the base of the keys in the core.config and
    core.state dictionaries.

    If we started the service, the service is stopped by doing "service
    init_script stop" or "systemctl stop service_name". We also check
    that the sentinel file, if there was one, no longer exists.

    Globals used:
    core.config[service_name.init-script] is used to get the name of the
    init script. If not set, service_name is used.
    core.config[service_name.sentinel-file] is used to get the path of the
    sentinel file.
    core.state[service_name.started-service] is used to determine if we started
    the service. After shutdown, this is set to False.

    """
    init_script = _init_script_name(service_name)

    if not core.state.get(service_name + '.started-service'):
        core.skip('did not start service ' + service_name)
        return

    if core.el_release() >= 7:
        command = ('systemctl', 'stop', init_script)
    else:
        command = ('service', init_script, 'stop')
    core.check_system(command, 'Stop ' + service_name + ' service')

    sentinel_file = core.config.get(service_name + '.sentinel-file')
    if sentinel_file:
        assert not os.path.exists(sentinel_file), "%(service_name)s sentinel file still exists at %(sentinel_file)s" % locals()

    core.state[service_name + '.started-service'] = False

def is_running(service_name, init_script=None, timeout=5):
    """Detect if a service is running via an init script

    Globals used:
    core.config[service_name.init-script] is used to get the name of the
    init script. If not set, service_name is used.
    """
    init_script = _init_script_name(service_name, init_script)

    if core.el_release() >= 7:
        command = ('systemctl', 'is-active', init_script)
    else:
        command = ('service', init_script, 'status')

    timer = 0
    status = None
    while timer < timeout:
        # Don't exit loop based on status since we use this function
        # to also check to ensure that the service gets stopped properly
        status, _, _ = core.system(command, 'Checking status of ' + service_name + ' service')
        time.sleep(1)
        timer += 1

    return status == 0

