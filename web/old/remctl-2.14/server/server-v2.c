/*
 * Protocol v2, server implementation.
 *
 * This is the server implementation of the new v2 protocol.
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
 * Given the client struct and the stream number the data is from, send a
 * protocol v2 output token to the client containing the data stored in the
 * buffer in the client struct.  Returns true on success, false on failure
 * (and logs a message on failure).
 */
bool
server_v2_send_output(struct client *client, int stream)
{
    gss_buffer_desc token;
    char *p;
    OM_uint32 tmp, major, minor;
    int status;

    /* Allocate room for the total message. */
    token.length = 1 + 1 + 1 + 4 + client->outlen;
    token.value = xmalloc(token.length);

    /*
     * Fill in the header (version, type, stream, length, and data) and then
     * the data.
     */
    p = token.value;
    *p = 2;
    p++;
    *p = MESSAGE_OUTPUT;
    p++;
    *p = stream;
    p++;
    tmp = htonl(client->outlen);
    memcpy(p, &tmp, 4);
    p += 4;
    memcpy(p, client->output, client->outlen);

    /* Send the token. */
    status = token_send_priv(client->fd, client->context,
                 TOKEN_DATA | TOKEN_PROTOCOL, &token, &major, &minor);
    if (status != TOKEN_OK) {
        warn_token("sending output token", status, major, minor);
        free(token.value);
        client->fatal = true;
        return false;
    }
    free(token.value);
    return true;
}


/*
 * Given the client struct and the exit status, send a protocol v2 status
 * token to the client.  Returns true on success, false on failure (and logs a
 * message on failure).
 */
bool
server_v2_send_status(struct client *client, int exit_status)
{
    gss_buffer_desc token;
    char buffer[1 + 1 + 1];
    OM_uint32 major, minor;
    int status;

    /* Build the status token. */
    token.length = 1 + 1 + 1;
    token.value = &buffer;
    buffer[0] = 2;
    buffer[1] = MESSAGE_STATUS;
    buffer[2] = exit_status;

    /* Send the token. */
    status = token_send_priv(client->fd, client->context,
                 TOKEN_DATA | TOKEN_PROTOCOL, &token, &major, &minor);
    if (status != TOKEN_OK) {
        warn_token("sending status token", status, major, minor);
        client->fatal = true;
        return false;
    }
    return true;
}


/*
 * Given the client struct, an error code, and an error message, send a
 * protocol v2 error token to the client.  Returns true on success, false on
 * failure (and logs a message on failure).
 */
bool
server_v2_send_error(struct client *client, enum error_codes code,
                     const char *message)
{
    gss_buffer_desc token;
    char *p;
    OM_uint32 tmp, major, minor;
    int status;

    /* Build the error token. */
    token.length = 1 + 1 + 4 + 4 + strlen(message);
    token.value = xmalloc(token.length);
    p = token.value;
    *p = 2;
    p++;
    *p = MESSAGE_ERROR;
    p++;
    tmp = htonl(code);
    memcpy(p, &tmp, 4);
    p += 4;
    tmp = htonl(strlen(message));
    memcpy(p, &tmp, 4);
    p += 4;
    memcpy(p, message, strlen(message));

    /* Send the token. */
    status = token_send_priv(client->fd, client->context,
                 TOKEN_DATA | TOKEN_PROTOCOL, &token, &major, &minor);
    if (status != TOKEN_OK) {
        warn_token("sending error token", status, major, minor);
        free(token.value);
        client->fatal = true;
        return false;
    }
    free(token.value);
    return true;
}


/*
 * Given the client struct, send a protocol v2 version token to the client.
 * This is the response to a higher version number than we understand.
 * Returns true on success, false on failure (and logs a message on failure).
 */
static bool
server_v2_send_version(struct client *client)
{
    gss_buffer_desc token;
    char buffer[1 + 1 + 1];
    OM_uint32 major, minor;
    int status;

    /* Build the version token. */
    token.length = 1 + 1 + 1;
    token.value = &buffer;
    buffer[0] = 2;
    buffer[1] = MESSAGE_VERSION;
    buffer[2] = 2;

    /* Send the token. */
    status = token_send_priv(client->fd, client->context,
                 TOKEN_DATA | TOKEN_PROTOCOL, &token, &major, &minor);
    if (status != TOKEN_OK) {
        warn_token("sending version token", status, major, minor);
        client->fatal = true;
        return false;
    }
    return true;
}


/*
 * Receive a new token from the client, handling reporting of errors.  Takes
 * the client struct and a pointer to storage for the token.  Returns TOKEN_OK
 * on success, TOKEN_FAIL_EOF if the other end has gone away, and a different
 * error code on a recoverable error.
 */
static int
server_v2_read_token(struct client *client, gss_buffer_t token)
{
    OM_uint32 major, minor;
    int status, flags;
    
    status = token_recv_priv(client->fd, client->context, &flags, token,
                             TOKEN_MAX_LENGTH, &major, &minor);
    if (status != TOKEN_OK) {
        warn_token("receiving command token", status, major, minor);
        if (status != TOKEN_FAIL_EOF)
            if (!server_send_error(client, ERROR_BAD_TOKEN, "Invalid token"))
                return TOKEN_FAIL_EOF;
    }
    return status;
}


/*
 * Handles a single token from the client, responding or running a command as
 * appropriate.  Returns true if we should continue, false if an error
 * occurred or QUIT was received and we should stop processing tokens.
 */
static bool
server_v2_handle_token(struct client *client, struct config *config,
                       gss_buffer_t token)
{
    char *p;
    size_t length, total;
    struct iovec **argv = NULL;
    char *buffer = NULL;
    int status;
    OM_uint32 minor;
    bool result = false;
    bool allocated = false;
    bool continued = false;

    /*
     * Loop on tokens until we have a complete command, allowing for continued
     * commands.  We're going to accumulate the full command in buffer until
     * we've seen all of it.  If the command isn't continued, we can use the
     * token as the buffer.
     */
    total = 0;
    do {
        p = token->value;
        if (p[0] != 2) {
            result = server_v2_send_version(client);
            goto fail;
        } else if (p[1] == MESSAGE_QUIT) {
            debug("quit received, closing connection");
            result = false;
            goto fail;
        } else if (p[1] != MESSAGE_COMMAND) {
            warn("unknown message type %d from client", (int) p[1]);
            result = server_send_error(client, ERROR_UNKNOWN_MESSAGE,
                                       "Unknown message");
            goto fail;
        }
        p += 2;
        client->keepalive = p[0] ? true : false;

        /* Check the data size. */
        if (token->length > TOKEN_MAX_DATA) {
            warn("command data length %lu exceeds 64KB",
                 (unsigned long) token->length);
            result = server_send_error(client, ERROR_TOOMUCH_DATA,
                                       "Too much data");
            goto fail;
        }

        /* Make sure the continuation is sane. */
        if ((p[1] == 1 && continued) || (p[1] > 1 && !continued) || p[1] > 3) {
            warn("bad continue status %d", (int) p[1]);
            result = server_send_error(client, ERROR_BAD_COMMAND,
                                       "Invalid command token");
            goto fail;
        }
        continued = (p[1] == 1 || p[1] == 2);

        /*
         * Read the token data.  If the command is continued *or* if buffer is
         * non-NULL (meaning the command was previously continued), we copy
         * the data into the buffer.
         */
        p += 2;
        length = token->length - (p - (char *) token->value);
        if (continued || buffer != NULL) {
            if (buffer == NULL)
                buffer = xmalloc(length);
            else
                buffer = xrealloc(buffer, total + length);
            allocated = true;
            memcpy(buffer + total, p, length);
            total += length;
        }

        /*
         * If the command was continued, we have to read the next token.
         * Otherwise, if buffer is NULL (no continuation), we just use this
         * token as the complete buffer.
         */
        if (continued) {
            gss_release_buffer(&minor, token);
            status = server_v2_read_token(client, token);
            if (status == TOKEN_FAIL_EOF)
                result = false;
            else if (status != TOKEN_OK)
                result = true;
            if (status != TOKEN_OK)
                goto fail;
        } else if (buffer == NULL) {
            buffer = p;
            total = length;
        }
    } while (continued);

    /*
     * Okay, we now have a complete command that was possibly spread over
     * multiple tokens.  Now we can parse it.
     */
    argv = server_parse_command(client, buffer, total);
    if (allocated)
        free(buffer);
    if (argv == NULL)
        return !client->fatal;

    /* We have a command.  Now do the heavy lifting. */
    server_run_command(client, config, argv);
    server_free_command(argv);
    return !client->fatal;

fail:
    if (allocated)
        free(buffer);
    return result;
}


/*
 * Takes the client struct and the server configuration and handles client
 * requests.  Reads messages from the client, checking commands against the
 * ACLs and executing them when appropriate, until the connection is
 * terminated.
 */
void
server_v2_handle_commands(struct client *client, struct config *config)
{
    gss_buffer_desc token;
    OM_uint32 minor;
    int status;

    /* Loop receiving messages until we're finished. */
    do {
        status = server_v2_read_token(client, &token);
        if (status == TOKEN_FAIL_EOF)
            break;
        else if (status != TOKEN_OK)
            continue;
        if (!server_v2_handle_token(client, config, &token)) {
            gss_release_buffer(&minor, &token);
            break;
        }
        gss_release_buffer(&minor, &token);
    } while (client->keepalive);
}
