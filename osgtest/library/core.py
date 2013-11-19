"""Support and convenience functions for tests."""


import os
import os.path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import socket

from osgtest.library import osgunittest

# ------------------------------------------------------------------------------
# Module attributes
# ------------------------------------------------------------------------------

# Global configuration dictionary.  The intent here is to store configuration
# for the test run.  Someday, we may even load this configuration from a file,
# or something like that.  For now, test modules should only add new entries to
# this dictionary, neither modifying nor deleting existing ones.
config = {}
config['user.home'] = '/var/home'
config['system.mapfile'] = '/etc/grid-security/grid-mapfile'

# Global state dictionary.  Other modules may add, read, change, and delete the
# keys stored herein.  At the moment, no checking is done on its contents, so
# individual tests should be careful about using it.  The recommendation is to
# prefix each key with "COMP.", where "COMP" is a short lowercase string that
# indicates which component the test belongs to, or "general." for truly cross-
# cutting objects.
state = {}

# Global command-line options.  This should be merged into the config object,
# eventually.
options = None

# "Internal" attributes for use within this module.
_log = None
_log_filename = None
_last_log_had_output = True
_el_release = None


# ------------------------------------------------------------------------------
# Global Functions
# ------------------------------------------------------------------------------

def start_log():
    """Creates the detailed log file; not for general use."""
    global _log_filename, _log
    (log_fd, _log_filename) = tempfile.mkstemp()
    _log = os.fdopen(log_fd, 'w')
    _log.write(('-' * 80) + '\n')
    _log.write('OSG-TEST LOG\n')
    _log.write('Start time: ' + time.strftime('%Y-%m-%d %H:%M:%S') + '\n\n')
    _log.write('Options:\n')
    _log.write('  - Add user: %s\n' % str(options.adduser))
    _log.write('  - Config file: %s\n' % options.config)
    _log.write('  - Dump output: %s\n' % str(options.dumpout))
    _log.write('  - Dump file: %s\n' % options.dumpfile)
    _log.write('  - Install: %s\n' % ', '.join(options.packages))
    _log.write('  - Update repo: %s\n' % options.updaterepo)
    _log.write('  - Update release: %s\n' % options.updaterelease)
    _log.write('  - No cleanup: %s\n' % str(options.skip_cleanup))
    _log.write('  - Extra repos: %s\n' % ', '.join(options.extrarepos))
    _log.write('  - Print test names: %s\n' % str(options.printtest))
    _log.write('  - Skip tests: %s\n' % str(options.skiptests))
    _log.write('  - Test user: %s\n' % options.username)
    _log.write('  - Timeout: %s\n' % str(options.timeout))
    _log.write('  - Create hostcert: %s\n' % str(options.hostcert))
    _log.write('  - Backup MySQL: %s\n' % str(options.backupmysql))
    _log.flush()

def log_message(message):
    """Writes the message to the detailed log file.

    Following the format of the log file, the message is preceded by 'message:'
    and the current timestamp.  Note that the log file is only visible using the
    '-d' command-line option.
    """
    global _last_log_had_output
    if _last_log_had_output:
        _log.write('\n')
    _log.write('message: ')
    _log.write(time.strftime('%Y-%m-%d %H:%M:%S: '))
    _log.write(message + '\n')
    _last_log_had_output = False

def end_log():
    """Closes the detailed log file; not for general use."""
    _log.close()

def dump_log(outfile=None):
    if outfile is None:
        logfile = open(_log_filename, 'r')
        print '\n'
        for line in logfile:
            print line.rstrip('\n')
        logfile.close()
    else:
        shutil.copy(_log_filename, outfile)

def remove_log():
    """Removes the detailed log file; not for general use."""
    os.remove(_log_filename)

def monitor_file(filename, old_stat, sentinel, timeout):
    """Monitors a file for the sentinel regex

    This function tries to monitor a growing file for a bit of text.  Because
    the file may already exist prior to the monitoring process, the second
    argument is the object that resulted from an os.stat() call prior to the
    event that is being monitored; the monitoring will start at the file
    position given by the length of the old stat, when appropriate.

    The monitoring will last no longer than the given timeout, in seconds.  If
    the file exists (or comes to exist) and the text is found within the timeout
    period, the function returns the tuple (line, delay), where 'line' is the
    complete line on which the sentinel occurred and 'delay' is the number of
    seconds that passed before the sentinel was found.  Otherwise, the tuple
    (None, None) is returned.

    NOTE: This function handles logrotation when files are moved to a separate
    location and a new file is started in its place. However, it does NOT handle
    the copy and truncate method of logrotation (i.e. the file is copied to a
    different location and the original file is truncated to 0).
    """
    read_delay = 0.5 # Time to wait after reaching EOF and not finding the sentinel before trying again
    sentinel_regex = re.compile(sentinel)
    start_time = time.time()
    end_time = start_time + timeout
    monitored_file = None
    while time.time() <= end_time:
        if monitored_file is None:
            if not os.path.exists(filename):
                time.sleep(0.2)
                continue
            new_stat = os.stat(filename)
            if ((old_stat is None) or
                (new_stat.st_ino != old_stat.st_ino) or
                (new_stat.st_size < old_stat.st_size)):
                initial_position = 0
            else:
                initial_position = old_stat.st_size
            monitored_file = open(filename, 'r')
            monitored_file.seek(initial_position)

        where = monitored_file.tell()
        line = monitored_file.readline()
        if line:
            if sentinel_regex.search(line):
                monitored_file.close()
                return (line, time.time() - start_time)
        else:
            # If the file got moved from under us, close the old file. Previous iterations of the loop ensure that the
            # remaining contents of the old file got read. On the next iteration, the new file gets opened.
            if os.stat(filename).st_ino != new_stat.st_ino:
                monitored_file.close()
                old_stat = None
                monitored_file = None
            else:
                time.sleep(read_delay)
                monitored_file.seek(where)
    if monitored_file is not None:
        monitored_file.close()
    return (None, None)

def system(command, user=None, stdin=None, log_output=True, shell=False):
    """Runs a command and returns its exit status, stdout, and stderr.

    The command is provided as a list or tuple, unless the 'shell' argument is
    set to True, in which case the command should be a single string object.

    The command is run as root, unless the 'user' argument is set to True, in
    which case the command is run as the non-root user passed on the command
    line.

    If a 'stdin' string is given, it is piped into the command as its standard
    input.

    If 'log_output' is set to False, the standard output and standard error of
    the command are not written to the detailed log.

    If 'shell' is set to True, a shell subprocess is created and the command is
    run within that shell; in this case, the command should be given as a single
    string instead of a list or tuple.
    """
    return __run_command(command, user, stdin, subprocess.PIPE,
                         subprocess.PIPE, log_output, shell=shell)

def check_system(command, message, exit=0, user=None, stdin=None, shell=False):
    """Runs the command and checks its exit status code.

    Handles all of the common steps associated with running a system command:
    runs the command, checks its exit status code against the expected result,
    and raises an exception if there is an obvious problem.

    Returns a tuple of the standard output, standard error, and the failure
    message generated by diagnose().  See the system() function for more details
    about the command-line options.
    """
    status, stdout, stderr = system(command, user, stdin, shell=shell)
    fail = diagnose(message, status, stdout, stderr)
    assert status == exit, fail
    return stdout, stderr, fail

def rpm_is_installed(a_package):
    """Returns whether the RPM package is installed."""
    status, stdout, stderr = system(('rpm', '--query', a_package),
                                    log_output=False)
    return (status == 0) and stdout.startswith(a_package)

def dependency_is_installed(a_dependency):
    """Returns whether an RPM package providing a dependency is installed.

    Distinct from rpm_is_installed in that this handles virtual dependencies,
    such as 'grid-certificates'.
    """
    status, stdout, stderr = system(('rpm', '--query', '--whatprovides', a_dependency),
                                    log_output=False)
    return (status == 0) and not stdout.startswith('no package provides')

def installed_rpms():
    """Returns the list of all installed packages."""
    command = ('rpm', '--query', '--all', '--queryformat', r'%{NAME}\n')
    status, stdout, stderr = system(command, log_output=False)
    return set(re.split('\s+', stdout.strip()))

def skip(message=None):
    """Prints a 'SKIPPED' message to standard out."""
    sys.stdout.flush()
    if message:
        sys.stdout.write('SKIPPED (%s) ... ' % message)
    else:
        sys.stdout.write('SKIPPED ... ')
    sys.stdout.flush()

def missing_rpm(*packages):
    """Checks that all given RPM packages are installed.

    If any package is missing, list all missing packages in a skip() message.
    """
    if isinstance(packages[0], list) or isinstance(packages[0], tuple):
        packages = packages[0]

    missing = []    
    for package in packages:
        if not rpm_is_installed(package):
            missing.append(package)
    if len(missing) > 0:
        skip('missing %s' % ' '.join(missing))
        return True
    return False


def skip_ok_unless_installed(*packages_or_dependencies, **kwargs):
    """Check that all given RPM packages or dependencies are installed and skip
    the test if not.

    Accepts the following keyword arguments:
    - 'message' is the text to include in the Exception (a generic 'missing
      $package' will be used otherwise)
    - 'by_dependency' is a bool which, if True, will cause dependencies to be
      queried instead of packages
    Raise osgunittest.OkSkipException if packages/dependencies are missing,
    otherwise return None.
    """
    # Handle the keyword arguments. There is some magic here to make it work
    # with the variable number of arguments that we are using for
    # 'packages_or_dependencies'.  Make sure that we accept the argument not
    # being there, but also raise an error on unexpected keyword arguments.
    message = kwargs.pop('message', None)
    by_dependency = kwargs.pop('by_dependency', False)
    if kwargs:
        raise TypeError("skip_ok_unless_installed() got unexpected keyword argument(s) '%s'" %
                        ("', '".join(kwargs.keys())))

    if isinstance(packages_or_dependencies[0], list) or isinstance(packages_or_dependencies[0], tuple):
        packages_or_dependencies = packages_or_dependencies[0]

    missing = []
    if by_dependency:
        dependencies = packages_or_dependencies
        for dependency in dependencies:
            if not dependency_is_installed(dependency):
                missing.append(dependency)
    else:
        packages = packages_or_dependencies
        for package in packages:
            if not rpm_is_installed(package):
                missing.append(package)

    if len(missing) > 0:
        raise osgunittest.OkSkipException(message or 'missing %s' % ' '.join(missing))


def get_package_envra(package_name):
    """Query and return the ENVRA (Epoch, Name, Version, Release, Arch) of an
    installed package as a tuple. Can raise OSError if rpm does not return
    output in the right format.

    """
    command = ('rpm', '--query', package_name, "--queryformat=%{EPOCH} %{NAME} %{VERSION} %{RELEASE} %{ARCH} ")
    status, stdout, stderr = system(command)
    # Not checking stderr because signature warnings get written there and
    # we do not care about those.
    if (status != 0) or (stdout is None):
        raise OSError(status, stdout)

    envra = stdout.strip().split(' ')
    # On EL5 machines, both i386 and x86_64 versions of packages get installed, causing this function to always fail
    if (len(envra) == 10 and
        envra[0] == envra[5] and
        envra[1] == envra[6] and
        envra[2] == envra[7] and
        envra[3] == envra[8]):
            envra = envra[0:5]
    elif len(envra) != 5:
        raise OSError(status, stdout)
    (epoch, name, version, release, arch) = envra
    return (epoch, name, version, release, arch)




def diagnose(message, status, stdout, stderr):
    """Constructs a detailed failure message based on arguments."""
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

def __prepare_shell_argument(argument):
    if re.search(r'\W', argument):
        return "'" + re.sub(r"'", r"''\'", argument) + "'"
    return argument

def __run_command(command, use_test_user, a_input, a_stdout, a_stderr, log_output=True, shell=False):
    global _last_log_had_output

    # Preprocess command
    if shell:
        if not isinstance(command, str):
            command = ' '.join(command)
    elif not (isinstance(command, list) or isinstance(command, tuple)):
        raise TypeError, 'Need list or tuple, got %s' % (repr(command))
    if use_test_user:
        command = ['su', '-c', ' '.join(map(__prepare_shell_argument, command)), options.username]

    # Figure out stdin
    stdin = None
    if a_input is not None:
        stdin = subprocess.PIPE

    # Log
    if _last_log_had_output:
        _log.write('\n')
    _log.write('osgtest: ')
    _log.write(time.strftime('%Y-%m-%d %H:%M:%S: '))
    # HACK: print test name
    # Get the current test function name, the .py file it's in, and the line number from the call stack
    if options.printtest:
        stack = traceback.extract_stack()
        for stackentry in reversed(stack):
            filename, lineno, funcname, text = stackentry
            if re.search(r'(test_\d+|special).+\.py', filename):
                _log.write("%s:%s:%d: " % (os.path.basename(filename), funcname, lineno))
    _log.write(' '.join(__format_command(command)))

    # Run and return command
    p = subprocess.Popen(command, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell)
    (stdout, stderr) = p.communicate(a_input)

    # Log
    stdout_length = 0
    if stdout is not None:
        stdout_length = len(stdout)
    stderr_length = 0
    if stderr is not None:
        stderr_length = len(stderr)
    _log.write(' >>> %d %d %d\n' % (p.returncode, stdout_length, stderr_length))
    _last_log_had_output = False
    if log_output:
        if (stdout is not None) and (len(stdout.rstrip('\n')) > 0):
            _log.write('STDOUT:{\n')
            _log.write(stdout.rstrip('\n') + '\n')
            _log.write('STDOUT:}\n')
            _last_log_had_output = True
        if (stderr is not None) and (len(stderr.rstrip('\n')) > 0):
            _log.write('STDERR:{\n')
            _log.write(stderr.rstrip('\n') + '\n')
            _log.write('STDERR:}\n')
            _last_log_had_output = True
    _log.flush()

    return (p.returncode, stdout, stderr)


def el_release():
    """Return the major version of the Enterprise Linux release the system is
    running. SL/RHEL/CentOS 5.x will return 5; SL/RHEL/CentOS 6.x will return
    6.

    """
    global _el_release
    if not _el_release:
        try:
            try:
                release_file = open("/etc/redhat-release", 'r')
                release_text = release_file.read()
            finally:
                release_file.close()
            match = re.search(r"release (\d)", release_text)
            _el_release = int(match.group(1))
        except Exception, e: 
            _log.write("Couldn't determine redhat release: " + str(e) + "\n")
            sys.exit(1)
    return _el_release

def get_hostname():
    """
    Returns the hostname of the current system, returns None if it can't
    get the hostname
    """
    try:
        return socket.gethostbyaddr(socket.gethostname())[0]
    except Exception:
        return None
    return None
