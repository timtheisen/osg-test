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

last_log_was_brief = False

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

def command(command, user=None, stdin=None, no_output=False,
            brief_output=False):
    (status, stdout, stderr) = __run_command(command, user, stdin,
                                             subprocess.PIPE, subprocess.STDOUT,
                                             no_output, brief_output)
    print stdout.rstrip(),
    return status

def syspipe(command, user=None, stdin=None, no_output=False,
            brief_output=False):
    return __run_command(command, user, stdin, subprocess.PIPE,
                         subprocess.PIPE, no_output, brief_output)

def rpm_is_installed(a_package):
    (status, stdout, stderr) = syspipe(['rpm', '--query', a_package],
                                       brief_output=True)
    return (status == 0) and stdout.startswith(a_package)

def installed_rpms():
    command = ['rpm', '--query', '--all', '--queryformat', r'%{NAME}\n']
    (status, stdout, stderr) = syspipe(command, no_output=True)
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

def __run_command(command, use_test_user, a_input, a_stdout, a_stderr,
                  no_output=False, brief_output=False):
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
    log_time_string = time.strftime('%Y-%m-%d %H:%M:%S')
    log_command_string = ' '.join(__format_command(command))
    if brief_output:
        if not osgtest.last_log_was_brief:
            osgtest.log.write('\n' + ('-' * 80) + '\n\n')
        osgtest.last_log_was_brief = True
        osgtest.log.write('%s: %s ' % (log_time_string, log_command_string))
    else:
        osgtest.last_log_was_brief = False
        osgtest.log.write('\n' + ('-' * 80) + '\n\n')
        osgtest.log.write('TIME: %s\n' % (log_time_string))
        osgtest.log.write('COMMAND: %s\n' % (log_command_string))

    # Run and return command
    p = subprocess.Popen(command, stdin=stdin, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    (stdout, stderr) = p.communicate(a_input)

    if brief_output:
        osgtest.log.write('(%d)\n' % (p.returncode))
    else:
        osgtest.log.write('EXIT STATUS: %d\n' % p.returncode)
        osgtest.log.write('STANDARD OUTPUT:')
        if no_output:
            osgtest.log.write(' [suppressed]\n')
        elif (stdout is None) or (len(stdout.rstrip('\n')) == 0):
            osgtest.log.write(' [none]\n')
        else:
            osgtest.log.write('\n' + stdout.rstrip('\n') + '\n')
        osgtest.log.write('STANDARD ERROR:')
        if no_output:
            osgtest.log.write(' [suppressed]\n')
        elif (stderr is None) or (len(stderr.rstrip('\n')) == 0):
            osgtest.log.write(' [none]\n')
        else:
            osgtest.log.write('\n' + stderr.rstrip('\n') + '\n')

    osgtest.log.flush()

    return (p.returncode, stdout, stderr)
