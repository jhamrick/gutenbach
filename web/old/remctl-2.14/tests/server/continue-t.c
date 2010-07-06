/*
 * Test suite for continued commands.
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


int
main(void)
{
    char *principal, *config, *path;
    struct remctl *r;
    struct remctl_output *output;
    pid_t remctld;
    static const char prefix_first[] = { 2, MESSAGE_COMMAND, 1, 1 };
    static const char prefix_next[] = { 2, MESSAGE_COMMAND, 1, 2 };
    static const char prefix_last[] = { 2, MESSAGE_COMMAND, 1, 3 };
    static const char data[] = {
        0, 0, 0, 3,
        0, 0, 0, 4, 't', 'e', 's', 't',
        0, 0, 0, 6, 's', 't', 'a', 't', 'u', 's',
        0, 0, 0, 1, '2'
    };
    char buffer[BUFSIZ];
    gss_buffer_desc token;
    OM_uint32 major, minor;
    int status;

    /* Unless we have Kerberos available, we can't really do anything. */
    if (chdir(getenv("SOURCE")) < 0)
        bail("can't chdir to SOURCE");
    principal = kerberos_setup();
    if (principal == NULL)
        skip_all("Kerberos tests not configured");
    plan(9);
    config = concatpath(getenv("SOURCE"), "data/conf-simple");
    path = concatpath(getenv("BUILD"), "../server/remctld");
    remctld = remctld_start(path, principal, config);

    /* Open a connection. */
    r = remctl_new();
    ok(r != NULL, "remctl_new");
    ok(remctl_open(r, "localhost", 14373, principal), "remctl_open");

    /* Send the command broken in the middle of protocol elements. */
    token.value = buffer;
    memcpy(buffer, prefix_first, sizeof(prefix_first));
    memcpy(buffer + sizeof(prefix_first), data, 2);
    token.length = sizeof(prefix_first) + 2;
    status = token_send_priv(r->fd, r->context, TOKEN_DATA | TOKEN_PROTOCOL,
                             &token, &major, &minor);
    is_int(TOKEN_OK, status, "first token sent okay");
    memcpy(buffer, prefix_next, sizeof(prefix_next));
    memcpy(buffer + sizeof(prefix_next), data + 2, 4);
    token.length = sizeof(prefix_next) + 4;
    status = token_send_priv(r->fd, r->context, TOKEN_DATA | TOKEN_PROTOCOL,
                             &token, &major, &minor);
    is_int(TOKEN_OK, status, "second token sent okay");
    memcpy(buffer, prefix_next, sizeof(prefix_next));
    memcpy(buffer + sizeof(prefix_next), data + 6, 13);
    token.length = sizeof(prefix_next) + 13;
    status = token_send_priv(r->fd, r->context, TOKEN_DATA | TOKEN_PROTOCOL,
                             &token, &major, &minor);
    is_int(TOKEN_OK, status, "third token sent okay");
    memcpy(buffer, prefix_last, sizeof(prefix_last));
    memcpy(buffer + sizeof(prefix_last), data + 19, sizeof(data) - 19);
    token.length = sizeof(prefix_next) + sizeof(data) - 19;
    status = token_send_priv(r->fd, r->context, TOKEN_DATA | TOKEN_PROTOCOL,
                             &token, &major, &minor);
    is_int(TOKEN_OK, status, "fourth token sent okay");
    r->ready = 1;
    output = remctl_output(r);
    ok(output != NULL, "got output");
    is_int(REMCTL_OUT_STATUS, output->type, "...of type status");
    is_int(2, output->status, "...with correct status");
    remctl_close(r);

    remctld_stop(remctld);
    kerberos_cleanup();
    return 0;
}
