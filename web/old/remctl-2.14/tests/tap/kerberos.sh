# Shell function library to initialize Kerberos credentials
#
# Written by Russ Allbery <rra@stanford.edu>
# Copyright 2009 Board of Trustees, Leland Stanford Jr. University
#
# See LICENSE for licensing terms.

# Set up Kerberos, including the ticket cache environment variable.  Bail out
# if not successful, return 0 if successful, and return 1 if Kerberos is not
# configured.  Sets the global principal variable to the principal to use.
kerberos_setup () {
    local keytab
    keytab=''
    for f in "$BUILD/data/test.keytab" "$SOURCE/data/test.keytab" ; do
        if [ -r "$f" ] ; then
            keytab="$f"
        fi
    done
    principal=''
    for f in "$BUILD/data/test.principal" "$SOURCE/data/test.principal" ; do
        if [ -r "$f" ] ; then
            principal=`cat "$BUILD/data/test.principal"`
        fi
    done
    if [ -z "$keytab" ] || [ -z "$principal" ] ; then
        return 1
    fi
    KRB5CCNAME="$BUILD/data/test.cache"; export KRB5CCNAME
    kinit -k -t "$keytab" "$principal" >/dev/null </dev/null
    status=$?
    if [ $status != 0 ] ; then
        kinit -t "$keytab" "$principal" >/dev/null </dev/null
        status=$?
    fi
    if [ $status != 0 ] ; then
        kinit -k -K "$keytab" "$principal" >/dev/null </dev/null
        status=$?
    fi
    if [ $status != 0 ] ; then
        bail "Can't get Kerberos tickets"
    fi
    return 0
}

# Clean up at the end of a test.  Currently only removes the ticket cache.
kerberos_cleanup () {
    rm -f "$BUILD/data/test.cache"
}
