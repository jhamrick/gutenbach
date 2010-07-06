# Shell function library for test cases.
#
# Written by Russ Allbery <rra@stanford.edu>
# Copyright 2009 Russ Allbery <rra@stanford.edu>
# Copyright 2006, 2007, 2008 Board of Trustees, Leland Stanford Jr. University
#
# See LICENSE for licensing terms.

# Print out the number of test cases we expect to run.
plan () {
    count=1
    echo "1..$1"
}

# Skip the entire test suite.  Should be run instead of plan.
skip_all () {
    local desc
    desc="$1"
    if [ -n "$desc" ] ; then
        echo "1..0 # skip $desc"
    else
        echo "1..0 # skip"
    fi
    exit 0
}

# ok takes a test description and a command to run and prints success if that
# command is successful, false otherwise.  The count starts at 1 and is
# updated each time ok is printed.
ok () {
    local desc
    desc="$1"
    if [ -n "$desc" ] ; then
        desc=" - $desc"
    fi
    shift
    if "$@" ; then
        echo ok $count$desc
    else
        echo not ok $count$desc
    fi
    count=`expr $count + 1`
}

# Skip the next test.  Takes the reason why the test is skipped.
skip () {
    echo "ok $count # skip $*"
    count=`expr $count + 1`
}

# Report the same status on a whole set of tests.  Takes the count of tests,
# the description, and then the command to run to determine the status.
ok_block () {
    local start end i desc
    i=$count
    end=`expr $count + $1`
    shift
    desc="$1"
    shift
    while [ "$i" -lt "$end" ] ; do
        ok "$desc" "$@"
        i=`expr $i + 1`
    done
}

# Skip a whole set of tests.  Takes the count and then the reason for skipping
# the test.
skip_block () {
    local start end
    i=$count
    end=`expr $count + $1`
    shift
    while [ "$i" -lt "$end" ] ; do
        skip "$@"
        i=`expr $i + 1`
    done
}

# Run a program expected to succeed, and print ok if it does and produces the
# correct output.  Takes the description, expected exit status, the expected
# output, the command to run, and then any arguments for that command.  Strip
# a colon and everything after it off the output if the expected status is
# non-zero, since this is probably a system-specific error message.
ok_program () {
    local desc w_status w_output output status
    desc="$1"
    shift
    w_status="$1"
    shift
    w_output="$1"
    shift
    output=`"$@" 2>&1`
    status=$?
    if [ "$w_status" -ne 0 ] ; then
        output=`echo "$output" | sed 's/^\([^:]*\):.*/\1/'`
    fi
    if [ $status = $w_status ] && [ x"$output" = x"$w_output" ] ; then
        ok "$desc" true
    else
        echo "#  saw: ($status) $output"
        echo "#  not: ($w_status) $w_output"
        ok "$desc" false
    fi
}

# Bail out with an error message.
bail () {
    echo 'Bail out!' "$@"
    exit 1
}
