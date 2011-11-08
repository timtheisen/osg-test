import os
import os.path
import osgtest
import re
import subprocess
import sys
import tempfile
import time


# ------------------------------------------------------------------------------
# Globally accessible data
# ------------------------------------------------------------------------------

HOME_DIR = '/var/home'

options = None
original_rpms = []
mapfile = None
mapfile_backup = None
log = None
log_filename = None

# ------------------------------------------------------------------------------
# Global Functions
# ------------------------------------------------------------------------------

def start_log():
    (log_fd, osgtest.log_filename) = tempfile.mkstemp()
    osgtest.log = os.fdopen(log_fd, 'w')
    osgtest.log.write(('-' * 80) + '\n')
    osgtest.log.write('OSG-TEST LOG\n')
    osgtest.log.write('Start time: ' + time.strftime('%Y-%m-%d %H:%M:%S') + '\n\n')
    osgtest.log.write('Options:\n')
    osgtest.log.write('  - Add user: %s\n' % str(osgtest.options.adduser))
    osgtest.log.write('  - Cleanup: %s\n' % str(osgtest.options.cleanup))
    osgtest.log.write('  - Install: %s\n' % ', '.join(osgtest.options.packages))
    osgtest.log.write('  - Extra repos: %s\n' % ', '.join(osgtest.options.extrarepos))
    osgtest.log.write('  - Run tests: %s\n' % str(osgtest.options.runtests))
    osgtest.log.write('  - Test user: %s\n' % osgtest.options.username)
    osgtest.log.write('  - Verbose: %s\n' % str(osgtest.options.verbose))
    osgtest.log.flush()

def end_log():
    osgtest.log.close()

def dump_log():
    logfile = open(osgtest.log_filename, 'r')
    print '\n'
    for line in logfile:
        print line.rstrip('\n')
    logfile.close()

def remove_log():
    os.remove(osgtest.log_filename)

def command(a_command, a_user=None, a_input=None, suppress=False):
    (status, stdout, stderr) = __run_command(a_command, a_user, a_input,
                                             subprocess.PIPE, subprocess.STDOUT,
                                             suppress)
    print stdout.rstrip(),
    return status

def syspipe(a_command, a_user=None, a_input=None, suppress=False):
    return __run_command(a_command, a_user, a_input, subprocess.PIPE,
                         subprocess.PIPE, suppress)

def rpm_is_installed(a_package):
    (status, stdout, stderr) = syspipe(['rpm', '--query', a_package])
    return (status == 0) and stdout.startswith(a_package)

def installed_rpms():
    command = ['rpm', '--query', '--all', '--queryformat', r'%{NAME}\n']
    (status, stdout, stderr) = syspipe(command, suppress=True)
    return set(re.split('\s+', stdout.strip()))

def skip(message=None):
    sys.stdout.flush()
    if message:
        sys.stdout.write('SKIPPED (%s) ... ' % message)
    else:
        sys.stdout.write('SKIPPED ... ')
    sys.stdout.flush()

def missing_rpm(a_packages):
    missing = []    
    for package in a_packages:
        if not osgtest.rpm_is_installed(package):
            missing.append(package)
    if len(missing) > 0:
        osgtest.skip('missing %s' % ' '.join(missing))
        return True
    return False

def diagnose(message, status, stdout, stderr):
    result = message + '\n'
    result += 'EXIT STATUS: %d\n' % (status)
    result += 'STANDARD OUTPUT:'
    if (stdout is None) or (len(stdout.rstrip('\n')) == 0):
        result += ' [none]\n'
    else:
        result += '\n' + stdout.rstrip('\n') + '\n'
    result += 'STANDARD ERROR:'
    if (stderr is None) or (len(stderr.rstrip('\n')) == 0):
        result += ' [none]\n'
    else:
        result += '\n' + stderr.rstrip('\n') + '\n'
    return result

def __format_command(command):
    result = []
    for part in command:
        if re.search(r"[' \\]", part):
            result.append("'" + part + "'")
        else:
            result.append(part)
    return result

def __run_command(command, use_test_user, a_input, a_stdout, a_stderr, suppress=False):
    # Preprocess command
    if not (isinstance(command, list) or isinstance(command, tuple)):
        raise TypeError, 'Need list or tuple, got %s' % str(type(command))
    if use_test_user:
        command = ['su', '-c', ' '.join(command), osgtest.options.username]

    # Figure out stdin
    stdin = None
    if a_input is not None:
        stdin = subprocess.PIPE

    # Log
    osgtest.log.write('\n' + ('-' * 80) + '\n\n')
    osgtest.log.write('TIME: ' + time.strftime('%Y-%m-%d %H:%M:%S') + '\n')
    osgtest.log.write('COMMAND: ' + ' '.join(__format_command(command)) + '\n')

    # Run and return command
    p = subprocess.Popen(command, stdin=stdin, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    (stdout, stderr) = p.communicate(a_input)

    osgtest.log.write('EXIT STATUS: %d\n' % p.returncode)

    osgtest.log.write('STANDARD OUTPUT:')
    if suppress:
        osgtest.log.write(' [suppressed]\n')
    elif (stdout is None) or (len(stdout.rstrip('\n')) == 0):
        osgtest.log.write(' [none]\n')
    else:
        osgtest.log.write('\n' + stdout.rstrip('\n') + '\n')
    osgtest.log.write('STANDARD ERROR:')
    if suppress:
        osgtest.log.write(' [suppressed]\n')
    elif (stderr is None) or (len(stderr.rstrip('\n')) == 0):
        osgtest.log.write(' [none]\n')
    else:
        osgtest.log.write('\n' + stderr.rstrip('\n') + '\n')
    osgtest.log.flush()

    return (p.returncode, stdout, stderr)
