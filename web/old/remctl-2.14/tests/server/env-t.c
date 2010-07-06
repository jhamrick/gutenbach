/*
 * Test suite for environment variables set by the server.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2006, 2009 Board of Trustees, Leland Stanford Jr. University
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
 * Run the remote env command with the given variable and return the value
 * from the server or NULL if there was an error.
 */
static char *
test_env(struct remctl *r, const char *variable)
{
    struct remctl_output *output;
    char *value = NULL;
    const char *command[] = { "test", "env", NULL, NULL };

    command[2] = variable;
    if (!remctl_command(r, command)) {
        notice("# remctl error %s", remctl_error(r));
        return NULL;
    }
    do {
        output = remctl_output(r);
        switch (output->type) {
        case REMCTL_OUT_OUTPUT:
            value = xstrndup(output->data, output->length);
            break;
        case REMCTL_OUT_STATUS:
            if (output->status != 0) {
                if (value != NULL)
                    free(value);
                notice("# test env returned status %d", output->status);
                return NULL;
            }
            if (value == NULL)
                value = xstrdup("");
            return value;
        case REMCTL_OUT_ERROR:
            if (value != NULL)
                free(value);
            notice("# test env returned error: %.*s", (int) output->length,
                   output->data);
            return NULL;
        case REMCTL_OUT_DONE:
            if (value != NULL)
                free(value);
            notice("# unexpected done token");
            return NULL;
        }
    } while (output->type == REMCTL_OUT_OUTPUT);
    return value;
}


int
main(void)
{
    char *principal, *config, *path, *expected, *value;
    struct remctl *r;
    pid_t remctld;

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
    expected = concat(principal, "\n", NULL);
    value = test_env(r, "REMUSER");
    is_string(expected, value, "value for REMUSER");
    free(value);
    value = test_env(r, "REMOTE_USER");
    is_string(expected, value, "value for REMOTE_USER");
    free(value);
    value = test_env(r, "REMOTE_ADDR");
    is_string("127.0.0.1\n", value, "value for REMOTE_ADDR");
    free(value);
    value = test_env(r, "REMOTE_HOST");
    ok(strcmp(value, "\n") == 0 || strstr(value, "localhost") != NULL,
       "value for REMOTE_HOST");
    free(value);
    remctl_close(r);

    remctld_stop(remctld);
    kerberos_cleanup();
    return 0;
}
