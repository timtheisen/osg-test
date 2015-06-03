"""Functions for performing common yum tasks.

The most important of these being the retry_command() function. This is 
necessary to overcome transient network issues, especially when running
the tests in VM universe at the CHTC.
"""

import re
import time

import osgtest.library.core as core

def clean_yum():
    deadline = time.time() + 3600
    pre = ('yum', '--enablerepo=*', 'clean')
    core.system(pre + ('all',))
    core.system(pre + ('expire-cache',))

def retry_command(command, timeout_seconds=3600):
    """Run a Yum command repeatedly until success, hard failure, or timeout.

    Run the given Yum command.  If it succeeds, return.  If it fails for a
    whitelisted reason, keep trying, otherwise return a failure message.  But,
    do not retry commands for longer than the timeout duration.
    """

    deadline = time.time() + timeout_seconds
    fail_msg, status, stdout, stderr = '', '', '', ''

    # EPEL released xrootd-compat (2/17/2015), which requires xrootd >= 4.1,
    # which is not available in 3.1
    if core.config['install.original-release-ver'] == '3.1':
        command.append('--exclude=xrootd-compat*')

    # Loop for retries
    while True:

        # Stop (re)trying if the deadline has passed
        if time.time() > deadline:
            fail_msg += "Retries terminated after timeout period" 
            break

        clean_yum()
        status, stdout, stderr = core.system(command)

        # Deal with success
        if status == 0:
            break

        # Deal with failures that can be retried
        elif yum_failure_can_be_retried(stdout):
            time.sleep(30)
            core.log_message("Retrying command")
            continue

        # Otherwise, we do not expect a retry to succeed, ever, so fail this
        # package
        else:
            fail_msg = core.diagnose("Command failed", status, stdout, stderr)
            break

    return fail_msg, status, stdout, stderr
                
def yum_failure_can_be_retried(output):
    """Scan yum output to see if a retry might succeed."""
    whitelist = [r'No more mirrors to try',
                 r'Timeout: <urlopen error timed out>',
                 r'Error communicating with server. The message was:\nNo route to host',
                 r'Timeout on.*Operation too slow. Less than 1 bytes/sec transfered the last 30 seconds',
                 r'Could not retrieve mirrorlist',
                 r"curl: \(7\) couldn't connect to host\nerror: skipping.*?transfer failed",
                 r'Error: Cannot retrieve repository metadata',
                 r'Error: Cannot retrieve metalink for repository',
                 r'Error: Temporary failure in name resolution']
    for regex in whitelist:
        if re.search(regex, output):
            return True
    return False

def get_transaction_id():
    """Grab the latest transaction ID from yum"""
    command = ('yum', 'history', 'info')
    history_out = core.check_system(command, 'Get yum Transaction ID')[0]
    m = re.search('Transaction ID : (\d*)', history_out)
    return m.group(1)

def parse_output_for_packages(yum_output):
    clean_output = yum_output.strip().split('\n')

    transaction_regexp = re.compile(r'\s+(Installing|Updating|Cleanup|Erasing)\s+:\s+\d*:?(\S+)\s+\d')
    xrootd_regexp = re.compile(r'\s+replacing\s+xrootd.*')
    for line in clean_output:
        # We need to track if xrootd was replaced with xrootd4 
        if xrootd_regexp.match(line):
            core.state['install.xrootd-replaced'] = True
        try:
            operation, pkg = transaction_regexp.match(line).groups()
        except AttributeError:
            # Catch exception when the line doesn't match our regex
            continue

        if operation == 'Installing' and pkg != 'kernel': # uninstalling kernel updates is a headache
            core.state['install.installed'].append(pkg)
        elif operation == 'Updating':
            core.state['install.updated'].append(pkg)
        elif operation == 'Cleanup' and pkg not in core.state['install.installed']:
            # Cleanup only occurs on upgrades/downgrades and if we didn't
            # install the package, it already existed on the machine
            core.state['install.os_updates'].append(pkg)
        elif operation == 'Erasing':
            try:
                core.state['install.installed'].remove(pkg)
            except ValueError:
                # We just removed a package that we didn't install, uh-oh!
                core.state['install.orphaned'].append(pkg)
            try:
                core.state['install.updated'].remove(pkg)
            except ValueError:
                # Package wasn't updated
                continue
