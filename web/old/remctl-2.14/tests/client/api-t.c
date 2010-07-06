/*
 * Test suite for the high-level remctl library API.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2006, 2007, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>

#include <signal.h>
#ifdef HAVE_SYS_SELECT_H
# include <sys/select.h>
#endif
#include <sys/time.h>
#include <sys/uio.h>
#include <sys/wait.h>

#include <client/remctl.h>
#include <client/internal.h>
#include <tests/tap/basic.h>
#include <tests/tap/kerberos.h>
#include <tests/tap/remctl.h>
#include <util/util.h>


/*
 * Takes the principal and the protocol version and runs a set of tests.  Due
 * to the compatibility layer, we should be able to run the same commands
 * regardless of the protocol (we're not testing any of the v2-specific
 * features here).
 */
static void
do_tests(const char *principal, int protocol)
{
    struct remctl *r;
    struct iovec *command;
    struct remctl_output *output;
    const char *test[] = { "test", "test", NULL };
    const char *error[] = { "test", "bad-command", NULL };
    const char *no_service[] = { "all", NULL };

    /* Open the connection. */
    r = remctl_new();
    ok(r != NULL, "protocol %d: remctl_new", protocol);
    is_string("no error", remctl_error(r), "remctl_error with no error");
    r->protocol = protocol;
    ok(remctl_open(r, "localhost", 14373, principal), "remctl_open");
    is_string("no error", remctl_error(r), "...still no error");

    /* Send a successful command. */
    ok(remctl_command(r, test), "remctl_command");
    is_string("no error", remctl_error(r), "...still no error");
    output = remctl_output(r);
    ok(output != NULL, "first output token is not null");
    if (output == NULL)
        ok(0, "...and has correct content");
    else {
        is_int(REMCTL_OUT_OUTPUT, output->type, "...and is right type");
        is_int(12, output->length, "...and is right length");
        if (output->data == NULL)
            ok(0, "...and is right data");
        else
            ok(memcmp("hello world\n", output->data, 11) == 0,
               "...and is right data");
        is_int(1, output->stream, "...and is right stream");
    }
    output = remctl_output(r);
    ok(output != NULL, "second output token is not null");
    is_int(REMCTL_OUT_STATUS, output->type, "...and is right type");
    is_int(0, output->status, "...and is right status");
    command = xcalloc(2, sizeof(struct iovec));
    command[0].iov_base = (char *) "test";
    command[0].iov_len = 4;
    command[1].iov_base = (char *) "test";
    command[1].iov_len = 4;
    ok(remctl_commandv(r, command, 2), "remctl_commandv");
    is_string("no error", remctl_error(r), "...still no error");
    output = remctl_output(r);
    ok(output != NULL, "first output token is not null");
    is_int(REMCTL_OUT_OUTPUT, output->type, "...and is right type");
    is_int(12, output->length, "...and is right length");
    if (output->data == NULL)
        ok(0, "...and is right data");
    else
        ok(memcmp("hello world\n", output->data, 11) == 0,
           "...and is right data");
    is_int(1, output->stream, "...and is right stream");
    output = remctl_output(r);
    ok(output != NULL, "second output token is not null");
    is_int(REMCTL_OUT_STATUS, output->type, "...and is right type");
    is_int(0, output->status, "...and is right status");

    /* Send a failing command. */
    ok(remctl_command(r, error), "remctl_command of error command");
    is_string("no error", remctl_error(r), "...no error on send");
    output = remctl_output(r);
    ok(output != NULL, "first output token is not null");
    if (protocol == 1) {
        is_int(REMCTL_OUT_OUTPUT, output->type,
               "...and is right protocol 1 type");
        is_int(16, output->length, "...and is right length");
        if (output->data == NULL)
            ok(0, "...and has the right error message");
        else
            ok(memcmp("Unknown command\n", output->data, 16) == 0,
               "...and has the right error message");
        is_int(1, output->stream, "...and is right stream");
        output = remctl_output(r);
        ok(output != NULL, "second output token is not null");
        is_int(REMCTL_OUT_STATUS, output->type, "...and is right type");
        is_int(-1, output->status, "...and is right status");
    } else {
        is_int(REMCTL_OUT_ERROR, output->type,
               "...and is right protocol 2 type");
        is_int(15, output->length, "...and is right length");
        if (output->data == NULL)
            ok(0, "...and has the right error message");
        else
            ok(memcmp("Unknown command", output->data, 15) == 0,
               "...and has the right error message");
        is_int(ERROR_UNKNOWN_COMMAND, output->error, "...and error number");
    }

    /* Send a command with no service. */
    ok(remctl_command(r, no_service), "remctl_command with no service");
    is_string("no error", remctl_error(r), "...and no error");
    output = remctl_output(r);
    ok(output != NULL, "...and non-null output token");
    is_int(REMCTL_OUT_OUTPUT, output->type, "...of correct type");
    is_int(12, output->length, "...and length");
    if (output->data == NULL)
        ok(0, "...and data");
    else
        ok(memcmp("hello world\n", output->data, 11) == 0, "...and data");
    is_int(1, output->stream, "...and stream");
    output = remctl_output(r);
    ok(output != NULL, "...and non-null second token");
    is_int(REMCTL_OUT_STATUS, output->type, "...of right type");
    is_int(0, output->status, "...and status");

    /* All done. */
    remctl_close(r);
    ok(1, "remctl_close didn't explode");
}


int
main(void)
{
    char *principal, *path, *config;
    pid_t remctld;
    struct remctl_result *result;
    const char *test[] = { "test", "test", NULL };
    const char *error[] = { "test", "bad-command", NULL };

    if (chdir(getenv("SOURCE")) < 0)
        bail("can't chdir to SOURCE");
    principal = kerberos_setup();
    if (principal == NULL)
        skip_all("Kerberos tests not configured");
    plan(98);
    config = concatpath(getenv("SOURCE"), "data/conf-simple");
    path = concatpath(getenv("BUILD"), "../server/remctld");
    remctld = remctld_start(path, principal, config);

    /* Run the basic protocol tests. */
    do_tests(principal, 1);
    do_tests(principal, 2);

    /*
     * We don't have a way of forcing the simple protocol to use a particular
     * protocol, so we always do it via protocol v2.  But if the above worked
     * with protocol v1, and this wrapper works with v2, everything should
     * have gotten tested.
     */
    result = remctl("localhost", 14373, principal, test);
    ok(result != NULL, "basic remctl API works");
    is_int(0, result->status, "...with correct status");
    is_int(0, result->stderr_len, "...and no stderr");
    is_int(12, result->stdout_len, "...and correct stdout_len");
    if (result->stdout_buf == NULL)
        ok(0, "...and correct data");
    else
        ok(memcmp("hello world\n", result->stdout_buf, 11) == 0,
           "...and correct data");
    ok(result->error == NULL, "...and no error");
    remctl_result_free(result);
    result = remctl("localhost", 14373, principal, error);
    ok(result != NULL, "remctl API with error works");
    is_int(0, result->status, "...with correct status");
    is_int(0, result->stdout_len, "...and no stdout");
    is_int(0, result->stderr_len, "...and no stderr");
    if (result->error == NULL)
        ok(0, "...and the right error string");
    else
        is_string("Unknown command", result->error,
                  "...and the right error string");
    remctl_result_free(result);

    remctld_stop(remctld);
    kerberos_cleanup();
    return 0;
}
