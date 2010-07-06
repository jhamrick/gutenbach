# Shell function library to start and stop remctld
#
# Written by Russ Allbery <rra@stanford.edu>
# Copyright 2009 Board of Trustees, Leland Stanford Jr. University
#
# See LICENSE for licensing terms.

# Start remctld.  Takes the path to remctld, which may be found via configure,
# and the path to the configuration file.
remctld_start () {
    local keytab principal
    rm -f "$BUILD/data/remctld.pid"
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
    if [ -n "$VALGRIND" ] ; then
        ( "$VALGRIND" --log-file=valgrind.%p --leak-check=full "$1" -m \
          -p 14373 -s "$principal" -P "$BUILD/data/remctld.pid" -f "$2" -d \
          -S -F -k "$keytab" &)
        [ -f "$BUILD/data/remctld.pid" ] || sleep 5
    else
        ( "$1" -m -p 14373 -s "$principal" -P "$BUILD/data/remctld.pid" \
          -f "$2" -d -S -F -k "$keytab" &)
    fi
    [ -f "$BUILD/data/remctld.pid" ] || sleep 1
    if [ ! -f "$BUILD/data/remctld.pid" ] ; then
        bail 'remctld did not start'
    fi
}

# Stop remctld and clean up.
remctld_stop () {
    if [ -f "$BUILD/data/remctld.pid" ] ; then
        kill -TERM `cat "$BUILD/data/remctld.pid"`
        rm -f "$BUILD/data/remctld.pid"
    fi
}
