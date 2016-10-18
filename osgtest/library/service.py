"""Utilities for starting and stopping init-based services."""
import time

import osgtest.library.core as core

def start(service_name):
    """
    Start a service via init script or systemd.

    'service_name' is used as the base of the keys in the core.config and
    core.state dictionaries.

    The service is started by doing "service service_name start" or "systemctl
    start service_name".

    The service is not started up if core.state[service_name.started-service] is
    True.

    The following globals are set:
    core.config[service_name.sentinel-file] is set to the value of sentinel_file,
    if specified.

    """
    if core.state.get(service_name + '.started-service'):
        core.skip('service ' + service_name + ' already running (flagged as started)')
        return

    if core.el_release() >= 7:
        command = ('systemctl', 'start', service_name)
    else:
        command = ('service', service_name, 'start')
    core.check_system(command, 'Start ' + service_name + ' service')
    core.state[service_name + '.started-service'] = True


def stop(service_name):
    """
    Stop a service via init script or systemd.

    'service_name' is used as the base of the keys in the core.config and
    core.state dictionaries.

    If we started the service, the service is stopped by doing "service
    service_name stop" or "systemctl stop service_name".

    Globals used:
    core.state[service_name.started-service] is used to determine if we started
    the service. After shutdown, this is set to False.

    """
    if not core.state.get(service_name + '.started-service'):
        core.skip('did not start service ' + service_name)
        return

    if core.el_release() >= 7:
        command = ('systemctl', 'stop', service_name)
    else:
        command = ('service', service_name, 'stop')
    core.check_system(command, 'Stop ' + service_name + ' service')
    core.state[service_name + '.started-service'] = False

def is_running(service_name, timeout=5):
    """
    Detect if a service, service_name, is running via init script or systemd
    """
    if core.el_release() >= 7:
        command = ('systemctl', 'is-active', service_name)
    else:
        command = ('service', service_name, 'status')

    status_rc = None
    for _ in range(0, timeout):
        # Don't exit loop based on status since we use this function to also
        # check to ensure that the service gets stopped properly
        status_rc, _, _ = core.system(command)
        time.sleep(1)

    return status_rc == 0

