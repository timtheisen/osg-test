"""Convenience functions to manage java versions """

EXPECTED_VERSION = '1.7.0'
JAVA_RPM = 'java-' + EXPECTED_VERSION + '-openjdk'
JAVAC_RPM = 'java-' + EXPECTED_VERSION + '-openjdk-devel'

import re
import osgtest.library.core as core

def _run_alternatives(java_type, a_input, message):
    command = ('alternatives', '--config', java_type)
    stdout, _, _ = core.check_system(command, message, stdin=a_input)
    return stdout

def is_openjdk_installed():
    if core.rpm_is_installed(JAVA_RPM):
        return True
    return False

def is_openjdk_devel_installed():
    if core.rpm_is_installed(JAVAC_RPM):
        return True
    return False

def select_ver(java_type, version):
    """Select the specified version of java in the alternatives"""
    alternatives = _run_alternatives(java_type, '\n', 'find %s version for selection' % java_type)
    selection = ''
    for alt in re.finditer(r'(\d+)\s+(\/.*\n)', alternatives):
        if version in alt.group(2):
            selection = alt.group(1)
    _run_alternatives(java_type, '%s\n' % selection, 'select %s version' % java_type)

def get_ver(java_type):
    """Find version of java that is currently selected in the alternatives"""
    current_java = _run_alternatives(java_type, '\n', 'find java version for selection')
    return re.search(r'\+.*\/(.*-\d\.\d\.\d[^\/]*)\/', current_java, re.MULTILINE).group(1)

def verify_ver(java_type, input_version):
    """Verify that the selected version of java is as expected."""
    command = (java_type, '-version')
    stdout, _, _ = core.check_system(command, 'verify %s version' % java_type)
    try:
        runtime_version = re.match('java.*(\d\.\d\.\d)', stdout).group(1)
    except AttributeError:
        return False
    return runtime_version in input_version
