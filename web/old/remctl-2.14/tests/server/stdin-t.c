/*
 * Test suite for the server passing data to programs on standard input.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2009 Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/uio.h>

#include <client/remctl.h>
#include <tests/tap/basic.h>
#include <tests/tap/kerberos.h>
#include <tests/tap/remctl.h>
#include <util/util.h>


/*
 * Run a stdin test case.  Takes the principal to use for the connection, the
 * first argument to the stdin program, and the data to send and ensures that
 * the client returns "Okay".
 */
static void
test_stdin(const char *principal, const char *test, const void *data,
           size_t length)
{
    struct remctl *r;
    struct iovec *command;
    struct remctl_output *output;

    command = xcalloc(4, sizeof(struct iovec));
    command[0].iov_base = (char *) "test";
    command[0].iov_len = strlen("test");
    command[1].iov_base = (char *) "stdin";
    command[1].iov_len = strlen("stdin");
    command[2].iov_base = (char *) test;
    command[2].iov_len = strlen(test);
    command[3].iov_base = (void *) data;
    command[3].iov_len = length;
    r = remctl_new();
    if (r == NULL)
        bail("cannot create remctl client");
    if (!remctl_open(r, "localhost", 14373, principal))
        bail("can't connect: %s", remctl_error(r));
    ok(remctl_commandv(r, command, 4), "sent command for %s", test);
    output = remctl_output(r);
    ok(output != NULL, "first output token is not null");
    is_int(REMCTL_OUT_OUTPUT, output->type, "...and is right type");
    is_int(strlen("Okay"), output->length, "...and is right length");
    if (output->data == NULL)
        ok(0, "...and is right data");
    else {
        notice("# data: %.*s", output->length, output->data);
        ok(memcmp("Okay", output->data, 4) == 0, "...and is right data");
    }
    is_int(1, output->stream, "...and is right stream");
    output = remctl_output(r);
    ok(output != NULL, "second output token is not null");
    is_int(REMCTL_OUT_STATUS, output->type, "...and is right type");
    is_int(0, output->status, "...and is right status");
    remctl_close(r);
}


int
main(void)
{
    char *principal, *config, *path, *buffer;
    pid_t remctld;

    /* Unless we have Kerberos available, we can't really do anything. */
    if (chdir(getenv("BUILD")) < 0)
        bail("can't chdir to BUILD");
    principal = kerberos_setup();
    if (principal == NULL)
        skip_all("Kerberos tests not configured");
    plan(9 * 9);
    config = concatpath(getenv("SOURCE"), "data/conf-simple");
    path = concatpath(getenv("BUILD"), "../server/remctld");
    remctld = remctld_start(path, principal, config);

    /* Run the tests. */
    test_stdin(principal, "read", "Okay", 4);
    test_stdin(principal, "write", "Okay", 4);
    test_stdin(principal, "exit", "Okay", 4);
    buffer = xmalloc(1024 * 1024);
    memset(buffer, 'A', 1024 * 1024);
    test_stdin(principal, "exit", buffer, 1024 * 1024);
    test_stdin(principal, "close", "Okay", 4);
    test_stdin(principal, "close", buffer, 1024 * 1024);
    test_stdin(principal, "nuls", "T\0e\0s\0t\0", 8);
    test_stdin(principal, "large", buffer, 1024 * 1024);
    test_stdin(principal, "delay", buffer, 1024 * 1024);

    remctld_stop(remctld);
    kerberos_cleanup();
    return 0;
}
