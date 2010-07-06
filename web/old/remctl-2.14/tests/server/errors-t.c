/*
 * Test suite for errors returned by the server.
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
#include <sys/wait.h>

#include <client/internal.h>
#include <client/remctl.h>
#include <tests/tap/basic.h>
#include <tests/tap/kerberos.h>
#include <tests/tap/remctl.h>
#include <util/util.h>


/*
 * Run the given command and return the error code from the server, or
 * ERROR_INTERNAL if the command unexpectedly succeeded or we didn't get an
 * error code.
 */
static int
test_error(struct remctl *r, const char *arg)
{
    struct remctl_output *output;
    const char *command[] = { "test", NULL, NULL };

    command[1] = arg;
    if (!remctl_command(r, command)) {
        notice("# remctl error %s", remctl_error(r));
        return ERROR_INTERNAL;
    }
    do {
        output = remctl_output(r);
        switch (output->type) {
        case REMCTL_OUT_OUTPUT:
            notice("# test %s returned output: %.*s", arg,
                   (int) output->length, output->data);
            break;
        case REMCTL_OUT_STATUS:
            notice("# test %s returned status %d", arg, output->status);
            return ERROR_INTERNAL;
        case REMCTL_OUT_ERROR:
            return output->error;
        case REMCTL_OUT_DONE:
            notice("# unexpected done token");
            return ERROR_INTERNAL;
        }
    } while (output->type == REMCTL_OUT_OUTPUT);
    return ERROR_INTERNAL;
}


/*
 * Try to send a command with 10K arguments to the server.  This should result
 * in ERROR_TOOMANY_ARGS given the current server limits.
 */
static int
test_excess_args(struct remctl *r)
{
    struct remctl_output *output;
    const char **command;
    size_t i;

    command = xmalloc((10 * 1024 + 3) * sizeof(const char *));
    command[0] = "test";
    command[1] = "echo";
    for (i = 2; i < (10 * 1024) + 2; i++)
        command[i] = "a";
    command[10 * 1024 + 2] = NULL;
    if (!remctl_command(r, command)) {
        notice("# remctl error %s", remctl_error(r));
        return ERROR_INTERNAL;
    }
    free(command);
    do {
        output = remctl_output(r);
        switch (output->type) {
        case REMCTL_OUT_OUTPUT:
            notice("# test echo returned output: %.*s", (int) output->length,
                   output->data);
            break;
        case REMCTL_OUT_STATUS:
            notice("# test echo returned status %d", output->status);
            return ERROR_INTERNAL;
        case REMCTL_OUT_ERROR:
            return output->error;
        case REMCTL_OUT_DONE:
            notice("# unexpected done token");
            return ERROR_INTERNAL;
        }
    } while (output->type == REMCTL_OUT_OUTPUT);
    return ERROR_INTERNAL;
}


int
main(void)
{
    char *principal, *config, *path;
    struct remctl *r;
    pid_t remctld;
    int status;

    /* Unless we have Kerberos available, we can't really do anything. */
    if (chdir(getenv("SOURCE")) < 0)
        bail("can't chdir to SOURCE");
    principal = kerberos_setup();
    if (principal == NULL)
        skip_all("Kerberos tests not configured");
    plan(4);
    config = concatpath(getenv("SOURCE"), "data/conf-simple");
    path = concatpath(getenv("BUILD"), "../server/remctld");
    remctld = remctld_start(path, principal, config);

    /* Run the tests. */
    r = remctl_new();
    if (!remctl_open(r, "localhost", 14373, principal))
        bail("cannot contact remctld");
    status = test_error(r, "bad-command");
    is_int(ERROR_UNKNOWN_COMMAND, status, "unknown command");
    status = test_error(r, "noauth");
    is_int(ERROR_ACCESS, status, "access denied");
    status = test_excess_args(r);
    is_int(ERROR_TOOMANY_ARGS, status, "too many arguments");
    status = test_error(r, NULL);
    is_int(ERROR_UNKNOWN_COMMAND, status, "unknown command");
    remctl_close(r);

    remctld_stop(remctld);
    kerberos_cleanup();
    return 0;
}
