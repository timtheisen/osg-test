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
                 r'Timeout on.*Operation too slow. Less than 1 bytes/sec transfered the last 30 seconds']
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
