import re
import time

import osgtest.library.core as core

def clean_yum():
    deadline = time.time() + 3600
    pre = ('yum', '--enablerepo=*', 'clean')
    core.system(pre + ('all',))
    core.system(pre + ('expire-cache',))

def retry_command(command, deadline):
    fail_msg, status, stdout, stderr = '', '', '', ''
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

        # Otherwise, we do not expect a retry to succeed, ever, so fail
        # this package
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
                 r'Could not retrieve mirrorlist.*error was\n\[Errno 14\] HTTP Error 500: Internal Server Error',
                 r'Error: Cannot retrieve repository metadata \(repomd\.xml\) for repository:.*Please verify its path and try again',
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
    install_regexp = re.compile(r'\s+Installing\s+:\s+\d*:?(\S+)\s+\d')
    update_regexp = re.compile(r'\s+Updating\s+:\s+\d*:?(\S+)\s+\d')
    # When packages are removed for dependencies or due to replacement by obsoletion
    erase_regexp = re.compile(r'\s+Erasing\s+:\s+\d*:?(\S+)\s+\d')
    for line in clean_output:
        install_matches = install_regexp.match(line)
        if install_matches is not None:
            core.state['install.installed'].append(install_matches.group(1))
            continue
        update_matches = update_regexp.match(line)
        if update_matches is not None:
            core.state['install.updated'].append(update_matches.group(1))
            continue
        erase_matches = erase_regexp.match(line)
        if erase_matches is not None:
            core.state['install.installed'].remove(erase_matches.group(1))
