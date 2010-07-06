/*
 * Protocol v1, server implementation.
 *
 * This is the server implementation of the old v1 protocol, which doesn't
 * support streaming, keep-alive, or many of the other features of the
 * current protocol.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Based on work by Anton Ushakov
 * Copyright 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/gssapi.h>
#include <portable/socket.h>
#include <portable/uio.h>

#include <server/internal.h>
#include <util/util.h>


/*
 * Given the client struct, a buffer of data to send, and the exit status of a
 * command, send a protocol v1 output token back to the client.  Returns true
 * on success and false on failure (and logs a message on failure).
 */
bool
server_v1_send_output(struct client *client, int exit_status)
{
    gss_buffer_desc token;
    char *p;
    OM_uint32 tmp, major, minor;
    int status;

    /* Allocate room for the total message. */
    token.length = 4 + 4 + client->outlen;
    token.value = xmalloc(token.length);

    /* Fill in the token. */
    p = token.value;
    tmp = htonl(exit_status);
    memcpy(p, &tmp, 4);
    p += 4;
    tmp = htonl(client->outlen);
    memcpy(p, &tmp, 4);
    p += 4;
    memcpy(p, client->output, client->outlen);
    
    /* Send the token. */
    status = token_send_priv(client->fd, client->context, TOKEN_DATA, &token,
                             &major, &minor);
    if (status != TOKEN_OK) {
        warn_token("sending output token", status, major, minor);
        free(token.value);
        return false;
    }
    free(token.value);
    return true;
}


/*
 * Takes the client struct and the server configuration and handles a client
 * request.  Reads a command from the client, checks the ACL, runs the command
 * if appropriate, and sends any output back to the client.
*/
void
server_v1_handle_commands(struct client *client, struct config *config)
{
    gss_buffer_desc token;
    OM_uint32 major, minor;
    struct iovec **argv = NULL;
    int status, flags;

    /* Receive the message. */
    status = token_recv_priv(client->fd, client->context, &flags, &token,
                             TOKEN_MAX_LENGTH, &major, &minor);
    if (status != TOKEN_OK) {
        warn_token("receiving command token", status, major, minor);
        if (status == TOKEN_FAIL_LARGE)
            server_send_error(client, ERROR_TOOMUCH_DATA, "Too much data");
        else if (status != TOKEN_FAIL_EOF)
            server_send_error(client, ERROR_BAD_TOKEN, "Invalid token");
        return;
    }

    /* Check the data size. */
    if (token.length > TOKEN_MAX_DATA) {
        warn("command data length %lu exceeds 64KB",
             (unsigned long) token.length);
        server_send_error(client, ERROR_TOOMUCH_DATA, "Too much data");
        gss_release_buffer(&minor, &token);
        return;
    }

    /*
     * Do the shared parsing of the message.  This code is identical to the
     * code for v2 (v2 just pulls more data off the front of the token first).
     */
    argv = server_parse_command(client, token.value, token.length);
    gss_release_buffer(&minor, &token);
    if (argv == NULL)
        return;

    /*
     * Check the ACL and existence of the command, run the command if
     * possible, and accumulate the output in the client struct.
     */
    server_run_command(client, config, argv);
    server_free_command(argv);
}
