/*
 * Test suite for version negotiation in the server.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2006, 2007, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/gssapi.h>

#include <signal.h>
#include <sys/wait.h>

#include <client/internal.h>
#include <client/remctl.h>
#include <tests/tap/basic.h>
#include <tests/tap/kerberos.h>
#include <tests/tap/remctl.h>
#include <util/util.h>

/* A command token to run test test. */
static const char token[] = {
    9, 1, 0, 0,
    0, 0, 0, 2,
    0, 0, 0, 4, 't', 'e', 's', 't',
    0, 0, 0, 4, 't', 'e', 's', 't'
};


int
main(void)
{
    char *principal, *config, *path;
    struct remctl *r;
    pid_t remctld;
    OM_uint32 major, minor;
    int flags, status;
    gss_buffer_desc tok;

    /* Unless we have Kerberos available, we can't really do anything. */
    if (chdir(getenv("SOURCE")) < 0)
        bail("can't chdir to SOURCE");
    principal = kerberos_setup();
    if (principal == NULL)
        skip_all("Kerberos tests not configured");
    plan(8);
    config = concatpath(getenv("SOURCE"), "data/conf-simple");
    path = concatpath(getenv("BUILD"), "../server/remctld");
    remctld = remctld_start(path, principal, config);

    /* Open the connection to the site. */
    r = remctl_new();
    ok(r != NULL, "remctl_new");
    ok(remctl_open(r, "localhost", 14373, principal), "remctl_open");

    /* Send the command token. */
    tok.length = sizeof(token);
    tok.value = (char *) token;
    status = token_send_priv(r->fd, r->context, TOKEN_DATA | TOKEN_PROTOCOL,
                             &tok, &major, &minor);
    if (status != TOKEN_OK)
        bail("cannot send token");

    /* Accept the remote token. */
    status = token_recv_priv(r->fd, r->context, &flags, &tok, 1024 * 64,
                             &major, &minor);
    is_int(TOKEN_OK, status, "received token correctly");
    is_int(TOKEN_DATA | TOKEN_PROTOCOL, flags, "token had correct flags");
    is_int(3, tok.length, "token had correct length");
    is_int(2, ((char *) tok.value)[0], "protocol version is 2");
    is_int(MESSAGE_VERSION, ((char *) tok.value)[1], "message version code");
    is_int(2, ((char *) tok.value)[2], "highest supported version is 2");

    /* Close things out. */
    remctl_close(r);

    remctld_stop(remctld);
    kerberos_cleanup();
    return 0;
}
