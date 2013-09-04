#!/bin/tcsh -x

set tarball_install_dir=$1

cd $tarball_install_dir
source ./setup.csh

if (! $?OSG_LOCATION) then
    echo 'OSG_LOCATION not set' > /dev/stderr
    exit 1
endif
if ($OSG_LOCATION != $PWD) then
    echo 'OSG_LOCATION not current dir' > /dev/stderr
    exit 1
endif

foreach var_to_test ( LD_LIBRARY_PATH PYTHONPATH PERL5LIB X509_CERT_DIR X509_VOMS_DIR VOMS_USERCONF )
    # Test each variable contains $OSG_LOCATION (or a subdir) somewhere.
    # Pipe printenv through grep to get something like
    #   VOMS_USERCONF=...
    # then search for either $OSG_LOCATION, or a subdir, either right at the
    # beginning or after a ':'.
    # Trying to use quotes instead of backslashing the metacharacters gave me
    # "invalid variable name" errors.
    printenv | grep \^${var_to_test}= | grep -qE \(=\|/\)${OSG_LOCATION}\(/\|\$\)
    if ($? != 0) then
        echo "${var_to_test} does not contain dirs under ${OSG_LOCATION}" > /dev/stderr
        exit 1
    endif
end

echo "$PYTHONPATH" | grep -qE "(^|/)$OSG_LOCATION/usr/lib(64)?/python2\.[4-6]/site-packages"
if ($? != 0) then
    echo 'PYTHONPATH does not contain site-packages dir' > /dev/stderr
    exit 1
endif

if (! $?LOCAL_VAR) then
    echo 'setup-local.csh not sourced' > /dev/stderr
    exit 1
endif

