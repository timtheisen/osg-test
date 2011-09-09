import os.path
import osgtest
import re
import subprocess
import sys


# ------------------------------------------------------------------------------
# Globally accessible data
# ------------------------------------------------------------------------------

HOME_DIR = '/var/home'

options = None
original_rpms = []


# ------------------------------------------------------------------------------
# Global Functions
# ------------------------------------------------------------------------------

def command(a_command, a_user=None, a_input=None):
    (status, stdout, stderr) = __run_command(a_command, a_user, a_input,
                                             subprocess.PIPE, subprocess.STDOUT)
    print stdout.rstrip(),
    return status

def syspipe(a_command, a_user=None, a_input=None):
    return __run_command(a_command, a_user, a_input, subprocess.PIPE,
                         subprocess.PIPE)

def rpm_is_installed(a_package):
    (status, stdout, stderr) = syspipe(['rpm', '--query', a_package])
    return (status == 0) and stdout.startswith(a_package)

def installed_rpms():
    command = ['rpm', '--query', '--all', '--queryformat', r'%{NAME}\n']
    (status, stdout, stderr) = syspipe(command)
    return set(re.split('\s+', stdout.strip()))

def skip(message=None):
    if message:
        sys.stdout.write('SKIPPED (%s) ... ' % message)
    else:
        sys.stdout.write('SKIPPED ... ')
    sys.stdout.flush()


def __run_command(a_command, a_user, a_input, a_stdout, a_stderr):
    # Preprocess command
    if not (isinstance(a_command, list) or isinstance(a_command, tuple)):
        raise TypeError, 'Need list or tuple, got %s' % str(type(a_command))
    command = list(a_command)
    if (a_user is not None) and (a_user != 'root') and (a_user != 0):
        command = ['su', '-c', ' '.join(command), osgtest.options.username]

    # Figure out stdin
    stdin = None
    if a_input is not None:
        stdin = subprocess.PIPE

    # Run and return command
    p = subprocess.Popen(command, stdin=stdin, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    (stdout, stderr) = p.communicate(a_input)
    return (p.returncode, stdout, stderr)
