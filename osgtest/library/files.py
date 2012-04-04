import glob
import os
import re
import shutil
import tempfile

import osgtest.library.core as core

_backup_suffix = '.osgtest-backup'
_files = {}

def _record_path(path):
    if path in _files:
        _files[path] += 1
    else:
        _files[path] = 1

def _remove_path(path):
    if path in _files:
        del _files[path]

def read(path, as_single_string=False):
    """Read the file at the path and return its contents."""
    the_file = open(path, 'r')
    if as_single_string:
        contents = the_file.read()
    else:
        contents = the_file.readlines()
    the_file.close()
    return contents

def write(path, contents, backup=True):
    """Write the contents to a file at the path."""
    # Write temporary file
    temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(path),
                                          prefix=os.path.basename(path),
                                          suffix='.osgtest-new')
    temp_file = os.fdopen(temp_fd, 'w')
    if isinstance(contents, list) or isinstance(contents, tuple):
        temp_file.writelines(contents)
    else:
        temp_file.write(contents)
    temp_file.close()
    _record_path(temp_path)

    # Copy ownership and permissions
    if os.path.exists(path):
        old_stat = os.stat(path)
        os.chown(temp_path, old_stat.st_uid, old_stat.st_gid)
        os.chmod(temp_path, old_stat.st_mode)

    # Back up existing file
    if os.path.exists(path) and backup:
        # We don't want to overwrite an existing backup.  Someday we might
        # have sequential backups, but for now we just want to save the state
        # of a file as it first exists (for most files this will be as it was
        # before we started running tests)
        backup_path = path + _backup_suffix
        if not os.path.exists(backup_path):
            shutil.copy2(path, backup_path)
            _record_path(backup_path)

    # Atomically move temporary file into final location
    os.rename(temp_path, path)
    _record_path(path)
    _remove_path(temp_path)

    core.log_message('Wrote %d bytes to %s' % (os.stat(path).st_size, path))


def append_line(path, line, backup=True, if_not_present=False):
    """ Append the supplied line to the given path.  A backup will
    be made by default.  If the lines should not be added if they are
    already present in the file pass if_not_present=True """

    old_contents = read(path)

    if if_not_present:
        if line in old_contents:
            return

    new_contents = old_contents + [line]
    write(path, new_contents)
    return


def restore(path):
    """Restores the path to its original state."""
    if path in _files and os.path.exists(path):
        os.remove(path)
        _remove_path(path)
        core.log_message('Removed test %s' % (path))
    backup_path = path + _backup_suffix
    if backup_path in _files and os.path.exists(backup_path):
        shutil.move(backup_path, path)
        _remove_path(backup_path)
        core.log_message('Restored original %s' % (path))

def remove(path):
    """Remove the path, which could be a file, empty directory, or file glob."""
    if re.search(r'[\]*?]', path):
        for glob_path in glob.glob(path):
            if os.path.isfile(glob_path):
                os.unlink(glob_path)
    elif os.path.isdir(path):
        if not os.listdir(path):
            os.rmdir(path)
        else:
            #shutil.rmtree(path)
            print "Cowardly refusing to delete a non-empty directory using rmtree"
            # Go ahead and try the rmdir to raise an exception
            os.rmdir(path)
    elif os.path.isfile(path):
        os.unlink(path)
