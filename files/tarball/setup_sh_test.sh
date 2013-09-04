#!/bin/sh -x

fail () {
    echo "$@" >&2
    exit 1
}

tarball_install_dir="${1?Usage: $0 tarball_install_dir}"

cd "$tarball_install_dir"
. ./setup.sh

if [ -z $OSG_LOCATION ]; then
    fail 'OSG_LOCATION not set'
fi
if [ $OSG_LOCATION != $PWD ]; then
    fail 'OSG_LOCATION not current dir'
fi

for var_to_test in LD_LIBRARY_PATH PYTHONPATH PERL5LIB X509_CERT_DIR X509_VOMS_DIR VOMS_USERCONF
do
    # Test each variable contains $OSG_LOCATION (or a subdir) somewhere.
    # Pipe set through grep to get something like
    #   VOMS_USERCONF=...
    # then search for either $OSG_LOCATION, or a subdir, either right at the
    # beginning or after a ':'.
    set | grep \^$var_to_test= | grep -qE "(=|:)$OSG_LOCATION(/|:|$)"
    if [ $? -ne 0 ]; then
        fail "$var_to_test does not contain dirs under $OSG_LOCATION"
    fi
done

echo "$PYTHONPATH" | grep -qE "(^|/)$OSG_LOCATION/usr/lib(64)?/python2\.[4-6]/site-packages"
if [ $? -ne 0 ]; then
    fail "PYTHONPATH does not contain site-packages dir"
fi

if [ -z $LOCAL_VAR ]; then
    fail "setup-local.sh not sourced"
fi

