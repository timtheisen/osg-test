import glob
import os
import re
import shutil
import tempfile

import osgtest.library.core as core


_backup_directory = '/usr/share/osg-test/backups'
_backups = {}


def read(path, as_single_string=False):
    """Read the file at the path and return its contents as a list or string."""
    the_file = open(path, 'r')
    if as_single_string:
        contents = the_file.read()
    else:
        contents = the_file.readlines()
    the_file.close()
    return contents


def preserve(path, owner):
    """Backup the file at path and remember it with the given owner."""
    if owner is None:
        raise ValueError('Must have owner string')

    backup_id = (path, owner)
    if backup_id in _backups:
        raise ValueError("Already have a backup of '%s' for '%s'" % (path, owner))

    backup_path = os.path.join(_backup_directory, os.path.basename(path) + '#' + owner)
    if os.path.exists(backup_path):
        raise ValueError("Backup already exists at '%s'" % (backup_path))

    if os.path.exists(path):
        if not os.path.isdir(_backup_directory):
            os.mkdir(_backup_directory)
        shutil.copy2(path, backup_path)
        _backups[backup_id] = backup_path
        core.log_message("Backed up '%s' as '%s'" % (path, backup_path))
    else:
        _backups[backup_id] = None

def write(path, contents, owner=None, backup=True):
    """Write the contents to a file at the path.

    The 'owner' argument (default: None), is a string that identifies the owner
    of the file.  If the 'backup' argument is True (default), then any existing
    file at the path will be backed up for later restoration.  However, because
    backups are identified in part by 'owner', if 'backup' is True, then 'owner'
    must be defined.  Typically, a caller specifies either 'backup=False' to
    turn off backups (not recommended) or 'owner=[some string]' to set the owner
    for the backup.
    """

    # The default arguments are invalid: Either "backup" must be false or the
    # "owner" must be specified.
    if (owner is None) and backup:
        raise ValueError('Must specify an owner or backup=False')

    # Write temporary file
    temp_fd, temp_path = tempfile.mkstemp(prefix=os.path.basename(path) + '.', suffix='.osgtest-new',
                                          dir=os.path.dirname(path))
    temp_file = os.fdopen(temp_fd, 'w')
    if isinstance(contents, list) or isinstance(contents, tuple):
        temp_file.writelines(contents)
    else:
        temp_file.write(contents)
    temp_file.close()

    # Copy ownership and permissions
    if os.path.exists(path):
        old_stat = os.stat(path)
        os.chown(temp_path, old_stat.st_uid, old_stat.st_gid)
        os.chmod(temp_path, old_stat.st_mode)

    # Back up existing file
    if backup:
        preserve(path, owner)

    # Atomically move temporary file into final location
    os.rename(temp_path, path)

    core.log_message('Wrote %d bytes to %s' % (os.stat(path).st_size, path))


def replace(path, old_line, new_line, owner=None, backup=True):
    """Replace an old line with a new line in given path.

    The 'owner' and 'backup' arguments are passed to write().
    """
    lines_to_write = []
    lines = read(path)
    for line in lines:
        if line.rstrip('\n') == old_line.rstrip('\n'):
            lines_to_write.append(new_line + '\n')
        else:
            lines_to_write.append(line.rstrip('\n') + '\n')
    write(path, lines_to_write, owner, backup)


def append(path, contents, force=False, owner=None, backup=True):
    """Append the contents to the given file.

    Normally, if the contents already exist in the file, no action is taken.
    However, if the force argument is True, then the extra contents are always
    appended.

    The 'owner' and 'backup' arguments are the same as in write().
    """
    # The default arguments are invalid: Either "backup" must be false or the
    # "owner" must be specified.
    if backup:
        if owner is None:
            raise ValueError('Must specify an owner or backup=False')
        preserve(path, owner)

    if os.path.exists(path):
        old_contents = read(path)
    else:
        old_contents = []

    if (not force) and (contents in old_contents):
        return

    new_contents = old_contents + [contents]
    write(path, new_contents, backup=False)


def restore(path, owner):
    """Restores the path to its state prior to being written by its owner."""
    backup_id = (path, owner)
    if backup_id not in _backups:
        raise ValueError("No backup of '%s' for '%s'" % (path, owner))

    if os.path.exists(path):
        os.remove(path)
        core.log_message('Removed test %s' % (path))
    backup_path = _backups[backup_id]
    if (backup_path is not None) and os.path.exists(backup_path):
        shutil.move(backup_path, path)
        core.log_message('Restored original %s' % (path))
    del _backups[backup_id]


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
