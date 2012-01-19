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
installed_rpm_list = []
mapfile = None
mapfile_backup = None
log = None
log_filename = None

last_log_had_output = True

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

def log_message(message):
    if osgtest.last_log_had_output:
        osgtest.log.write('\n')
    osgtest.log.write('message: ')
    osgtest.log.write(time.strftime('%Y-%m-%d %H:%M:%S: '))
    osgtest.log.write(message + '\n')
    osgtest.last_log_had_output = False

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

def monitor_file(filename, position, sentinel, timeout):
    start_time = time.time()
    end_time = start_time + timeout
    monitored_file = None
    while time.time() <= end_time:
        if monitored_file is None:
            if os.path.exists(filename):
                monitored_file = open(filename, 'r')
                monitored_file.seek(position)
            else:
                time.sleep(0.2)
                continue

        where = monitored_file.tell()
        line = monitored_file.readline()
        if line:
            if sentinel in line:
                monitored_file.close()
                return (line, time.time() - start_time)
        else:
            time.sleep(0.2)
            monitored_file.seek(where)
    return (None, None)

def command(command, user=None, stdin=None, log_output=True):
    (status, stdout, stderr) = __run_command(command, user, stdin,
                                             subprocess.PIPE, subprocess.STDOUT,
                                             log_output)
    print stdout.rstrip(),
    return status

def syspipe(command, user=None, stdin=None, log_output=True, shell=False):
    return __run_command(command, user, stdin, subprocess.PIPE,
                         subprocess.PIPE, log_output, shell=shell)

def rpm_is_installed(a_package):
    status, stdout, stderr = syspipe(('rpm', '--query', a_package),
                                     log_output=False)
    return (status == 0) and stdout.startswith(a_package)

def installed_rpms():
    command = ('rpm', '--query', '--all', '--queryformat', r'%{NAME}\n')
    status, stdout, stderr = syspipe(command, log_output=False)
    return set(re.split('\s+', stdout.strip()))

def skip(message=None):
    sys.stdout.flush()
    if message:
        sys.stdout.write('SKIPPED (%s) ... ' % message)
    else:
        sys.stdout.write('SKIPPED ... ')
    sys.stdout.flush()

def missing_rpm(*packages):
    missing = []    
    for package in packages:
        if not osgtest.rpm_is_installed(package):
            missing.append(package)
    if len(missing) > 0:
        osgtest.skip('missing %s' % ' '.join(missing))
        return True
    return False

def certificate_info(path):
    command = ('openssl', 'x509', '-noout', '-subject', '-issuer', '-in', path)
    status, stdout, stderr = syspipe(command)
    if (status != 0) or (stdout is None) or (stderr is not None):
        raise OSError(status, stderr)
    if len(stdout.strip()) == 0:
        raise OSError(status, stdout)
    subject_issuer_re = r'subject\s*=\s*([^\n]+)\nissuer\s*=\s*([^\n]+)\n'
    matches = re.match(subject_issuer_re, stdout)
    if matches is None:
        raise OSError(status, stdout)
    return (matches.group(1), matches.group(2))

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
    if isinstance(command, str):
        return [command]
    result = []
    for part in command:
        if part == '':
            result.append("''")
        elif re.search(r"[' \\]", part):
            result.append("'" + part + "'")
        else:
            result.append(part)
    return result

def __run_command(command, use_test_user, a_input, a_stdout, a_stderr,
                  log_output=True, shell=False):
    # Preprocess command
    if shell:
        if not isinstance(command, str):
            command = ' '.join(command)
    elif not (isinstance(command, list) or isinstance(command, tuple)):
        raise TypeError, 'Need list or tuple, got %s' % (repr(command))
    if use_test_user:
        command = ['su', '-c', ' '.join(command), osgtest.options.username]

    # Figure out stdin
    stdin = None
    if a_input is not None:
        stdin = subprocess.PIPE

    # Log
    if osgtest.last_log_had_output:
        osgtest.log.write('\n')
    osgtest.log.write('osgtest: ')
    osgtest.log.write(time.strftime('%Y-%m-%d %H:%M:%S: '))
    osgtest.log.write(' '.join(__format_command(command)))

    # Run and return command
    p = subprocess.Popen(command, stdin=stdin, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, shell=shell)
    (stdout, stderr) = p.communicate(a_input)

    # Log
    stdout_length = 0
    if stdout is not None:
        stdout_length = len(stdout)
    stderr_length = 0
    if stderr is not None:
        stderr_length = len(stderr)
    osgtest.log.write(' >>> %d %d %d\n' % (p.returncode, stdout_length, stderr_length))
    osgtest.last_log_had_output = False
    if log_output:
        if (stdout is not None) and (len(stdout.rstrip('\n')) > 0):
            osgtest.log.write('STDOUT:{\n')
            osgtest.log.write(stdout.rstrip('\n') + '\n')
            osgtest.log.write('STDOUT:}\n')
            osgtest.last_log_had_output = True
        if (stderr is not None) and (len(stderr.rstrip('\n')) > 0):
            osgtest.log.write('STDERR:{\n')
            osgtest.log.write(stderr.rstrip('\n') + '\n')
            osgtest.log.write('STDERR:}\n')
            osgtest.last_log_had_output = True
    osgtest.log.flush()

    return (p.returncode, stdout, stderr)
