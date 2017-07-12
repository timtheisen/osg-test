"""Utilities for starting and stopping init-based services."""
import time

import osgtest.library.core as core

STATUS_RUNNING = 0 # LSB: program is running or service is OK
STATUS_STOPPED = 3 # LSB: program is not running according to LSB init standards

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

def check_start(service_name, timeout=10):
    """
    Start a service, 'service_name' via init script or systemd and ensure that
    it starts running within a 'timeout' second window (default=10s)
    """
    start(service_name)
    assert is_running(service_name, timeout), "%s is not running" % service_name

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

def check_stop(service_name, timeout=10):
    """
    Stop a service, 'service_name' via init script or systemd and ensure that it
    stops running within a 'timeout' second window (default=10s)
    """
    stop(service_name)
    assert is_stopped(service_name, timeout), "%s is still running" % service_name

def status(service_name):
    """
    Return exit code of the 'service_name' init script or systemd status check
    """
    if core.el_release() >= 7:
        command = ('systemctl', 'is-active', service_name)
    else:
        command = ('service', service_name, 'status')

    status_rc, _, _ = core.system(command)
    return status_rc

def check_status(service_name, expected_status, timeout=10):
    """
    Return True if the exit code of the 'service_name' status check is
    expected_status before 'timeout' seconds. Otherwise, False.
    """
    timer = 0
    status_rc = None
    while timer < timeout and status_rc != expected_status:
        status_rc = status(service_name)
        time.sleep(1)
        timer += 1

    return status_rc == expected_status

def is_running(service_name, timeout=10):
    """
    Return True if 'service_name' is determined to be running via init script or
    systemd, according to LSB init standards, before 'timeout'
    seconds. Otherwise, False.
    """
    return check_status(service_name, STATUS_RUNNING, timeout)

def is_stopped(service_name, timeout=10):
    """
    Return True if service_name is properly stopped (exit code = 3) via init
    script or systemd, according to LSB, init standards, before 'timeout'
    seconds. Otherwise, False.
    """
    return check_status(service_name, STATUS_STOPPED, timeout)
