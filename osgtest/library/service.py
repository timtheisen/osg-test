"""Utilities for starting and stopping init-based services."""
import os
import re

import osgtest.library.core as core

def start(service_name, fail_pattern='FAILED', init_script=None, sentinel_file=None):
    """Start a service via an init script.

    'service_name' is used as the base of the keys in the core.config and
    core.state dictionaries. It is also used as the value of 'init_script',
    if it is not specified.

    The init script is run by doing "service init_script start". The regex
    'fail_pattern' is matched against stdout. If there is a match, startup is
    considered to have failed.

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
    if init_script is None:
        init_script = service_name
    core.config[service_name + '.init-script'] = init_script

    if sentinel_file and os.path.exists(sentinel_file):
        core.skip('service ' + service_name + ' already running (sentinel file found)')
        return
    if core.state.get(service_name + '.started-service'):
        core.skip('service ' + service_name + ' already running (flagged as started)')
        return
    core.state[service_name + '.started-service'] = False

    command = ('service', init_script, 'start')
    stdout, _, fail = core.check_system(command, 'Start ' + service_name + ' service')
    assert re.search(fail_pattern, stdout) is None, fail

    if sentinel_file:
        assert os.path.exists(sentinel_file), "%(service_name)s sentinel file not found at %(sentinel_file)s" % locals()
        core.config[service_name + '.sentinel-file'] = sentinel_file

    core.state[service_name + '.started-service'] = True


def stop(service_name, fail_pattern='FAILED'):
    """Stop a service via an init script.
    
    'service_name' is used as the base of the keys in the core.config and
    core.state dictionaries.

    If we started the service, the init script is run by doing "service
    init_script stop". The regex 'fail_pattern' is matched against stdout. If
    there is a match, shutdown is considered to have failed.  We also check
    that the sentinel file, if there was one, no longer exists.

    Globals used:
    core.config[service_name.init-script] is used to get the name of the
    init script. If not set, service_name is used.
    core.config[service_name.sentinel-file] is used to get the path of the
    sentinel file.
    core.state[service_name.started-service] is used to determine if we started
    the service. After shutdown, this is set to False.

    """
    init_script = core.config.get(service_name + '.init-script', service_name)

    if not core.state.get(service_name + '.started-service'):
        core.skip('did not start service ' + service_name)
        return

    command = ('service', init_script, 'stop')
    stdout, _, fail = core.check_system(command, 'Stop ' + service_name + ' service')
    assert re.search(fail_pattern, stdout) is None, fail

    sentinel_file = core.config.get(service_name + '.sentinel-file')
    if sentinel_file:
        assert not os.path.exists(sentinel_file), "%(service_name)s sentinel file still exists at %(sentinel_file)s" % locals()

    core.state[service_name + '.started-service'] = False


