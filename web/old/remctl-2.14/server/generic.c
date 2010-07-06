/*
 * Server implementation of generic protocol functions.
 *
 * These are the server protocol functions that can be shared between the v1
 * and v2 protocol.
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
 * Create a new client struct from a file descriptor and establish a GSS-API
 * context as a specified service with an incoming client and fills out the
 * client struct.  Returns a new client struct on success and NULL on failure,
 * logging an appropriate error message.
 */
struct client *
server_new_client(int fd, gss_cred_id_t creds)
{
    struct client *client;
    struct sockaddr_storage ss;
    socklen_t socklen;
    size_t length;
    char *buffer;
    gss_buffer_desc send_tok, recv_tok, name_buf;
    gss_name_t name = GSS_C_NO_NAME;
    gss_OID doid;
    OM_uint32 major = 0;
    OM_uint32 minor = 0;
    OM_uint32 acc_minor;
    int flags, status;
    static const OM_uint32 req_gss_flags
        = (GSS_C_MUTUAL_FLAG | GSS_C_CONF_FLAG | GSS_C_INTEG_FLAG);

    /* Create and initialize a new client struct. */
    client = xcalloc(1, sizeof(struct client));
    client->fd = fd;
    client->context = GSS_C_NO_CONTEXT;
    client->user = NULL;
    client->output = NULL;
    client->hostname = NULL;
    client->ipaddress = NULL;

    /* Fill in hostname and IP address. */
    socklen = sizeof(ss);
    if (getpeername(fd, (struct sockaddr *) &ss, &socklen) != 0) {
        syswarn("cannot get peer address");
        goto fail;
    }
    length = INET6_ADDRSTRLEN;
    buffer = xmalloc(length);
    client->ipaddress = buffer;
    status = getnameinfo((struct sockaddr *) &ss, socklen, buffer, length,
                         NULL, 0, NI_NUMERICHOST);
    if (status != 0) {
        syswarn("cannot translate IP address of client: %s",
                gai_strerror(status));
        goto fail;
    }
    length = NI_MAXHOST;
    buffer = xmalloc(length);
    status = getnameinfo((struct sockaddr *) &ss, socklen, buffer, length,
                         NULL, 0, NI_NAMEREQD);
    if (status == 0)
        client->hostname = buffer;
    else
        free(buffer);

    /* Accept the initial (worthless) token. */
    status = token_recv(client->fd, &flags, &recv_tok, TOKEN_MAX_LENGTH);
    if (status != TOKEN_OK) {
        warn_token("receiving initial token", status, major, minor);
        goto fail;
    }
    free(recv_tok.value);
    if (flags == (TOKEN_NOOP | TOKEN_CONTEXT_NEXT | TOKEN_PROTOCOL))
        client->protocol = 2;
    else if (flags == (TOKEN_NOOP | TOKEN_CONTEXT_NEXT))
        client->protocol = 1;
    else {
        warn("bad token flags %d in initial token", flags);
        goto fail;
    }

    /* Now, do the real work of negotiating the context. */
    do {
        status = token_recv(client->fd, &flags, &recv_tok, TOKEN_MAX_LENGTH);
        if (status != TOKEN_OK) {
            warn_token("receiving context token", status, major, minor);
            goto fail;
        }
        if (flags == TOKEN_CONTEXT)
            client->protocol = 1;
        else if (flags != (TOKEN_CONTEXT | TOKEN_PROTOCOL)) {
            warn("bad token flags %d in context token", flags);
            free(recv_tok.value);
            goto fail;
        }
        debug("received context token (size=%lu)",
              (unsigned long) recv_tok.length);
        major = gss_accept_sec_context(&acc_minor, &client->context, creds,
                    &recv_tok, GSS_C_NO_CHANNEL_BINDINGS, &name, &doid,
                    &send_tok, &client->flags, NULL, NULL);
        free(recv_tok.value);

        /* Send back a token if we need to. */
        if (send_tok.length != 0) {
            debug("sending context token (size=%lu)",
                  (unsigned long) send_tok.length);
            flags = TOKEN_CONTEXT;
            if (client->protocol > 1)
                flags |= TOKEN_PROTOCOL;
            status = token_send(client->fd, flags, &send_tok);
            if (status != TOKEN_OK) {
                warn_token("sending context token", status, major, minor);
                gss_release_buffer(&minor, &send_tok);
                goto fail;
            }
            gss_release_buffer(&minor, &send_tok);
        }

        /* Bail out if we lose. */
        if (major != GSS_S_COMPLETE && major != GSS_S_CONTINUE_NEEDED) {
            warn_gssapi("while accepting context", major, acc_minor);
            goto fail;
        }
        if (major == GSS_S_CONTINUE_NEEDED)
            debug("continue needed while accepting context");
    } while (major == GSS_S_CONTINUE_NEEDED);

    /* Make sure that the appropriate context flags are set. */
    if (client->protocol > 1) {
        if ((client->flags & req_gss_flags) != req_gss_flags) {
            warn("client did not negotiate appropriate GSS-API flags");
            goto fail;
        }
    }

    /* Get the display version of the client name and store it. */
    major = gss_display_name(&minor, name, &name_buf, &doid);
    if (major != GSS_S_COMPLETE) {
        warn_gssapi("while displaying client name", major, minor);
        goto fail;
    }
    major = gss_release_name(&minor, &name);
    client->user = xstrndup(name_buf.value, name_buf.length);
    gss_release_buffer(&minor, &name_buf);
    return client;

fail:
    if (client->context != GSS_C_NO_CONTEXT)
        gss_delete_sec_context(&minor, &client->context, GSS_C_NO_BUFFER);
    if (name != GSS_C_NO_NAME)
        gss_release_name(&minor, &name);
    if (client->ipaddress != NULL)
        free(client->ipaddress);
    if (client->hostname != NULL)
        free(client->hostname);
    free(client);
    return NULL;
}


/*
 * Free a client struct, including any resources that it holds.
 */
void
server_free_client(struct client *client)
{
    OM_uint32 major, minor;

    if (client->context != GSS_C_NO_CONTEXT) {
        major = gss_delete_sec_context(&minor, &client->context, NULL);
        if (major != GSS_S_COMPLETE)
            warn_gssapi("while deleting context", major, minor);
    }
    if (client->output != NULL)
        free(client->output);
    if (client->user != NULL)
        free(client->user);
    if (client->fd >= 0)
        close(client->fd);
    if (client->hostname != NULL)
        free(client->hostname);
    if (client->ipaddress != NULL)
        free(client->ipaddress);
    free(client);
}


/*
 * Receives a command token payload and builds an argv structure for it,
 * returning that as NULL-terminated array of pointers to struct iovecs.
 * Takes the client struct, a pointer to the beginning of the payload
 * (starting with the argument count), and the length of the payload.  If
 * there are any problems with the request, sends an error token, logs the
 * error, and then returns NULL.  Otherwise, returns the struct iovec array.
 */
struct iovec **
server_parse_command(struct client *client, const char *buffer, size_t length)
{
    OM_uint32 tmp;
    size_t argc, arglen, count;
    struct iovec **argv = NULL;
    const char *p = buffer;

    /* Read the argument count. */
    memcpy(&tmp, p, 4);
    argc = ntohl(tmp);
    p += 4;
    debug("argc is %lu", (unsigned long) argc);
    if (argc == 0) {
        warn("command with no arguments");
        server_send_error(client, ERROR_UNKNOWN_COMMAND, "Unknown command");
        return NULL;
    }
    if (argc > MAXCMDARGS) {
        warn("too large argc %lu in request message", (unsigned long) argc);
        server_send_error(client, ERROR_TOOMANY_ARGS, "Too many arguments");
        return NULL;
    }
    if (length - (p - buffer) < 4 * argc) {
        warn("command data too short");
        server_send_error(client, ERROR_BAD_COMMAND, "Invalid command token");
        return NULL;
    }
    argv = xcalloc(argc + 1, sizeof(struct iovec *));

    /*
     * Parse out the arguments and store them into a vector.  Arguments are
     * packed: (<arglength><argument>)+.  Make sure each time through the loop
     * that they didn't send more arguments than they claimed to have.
     */
    count = 0;
    while (p <= buffer + length - 4) {
        if (count >= argc) {
            warn("sent more arguments than argc %lu", (unsigned long) argc);
            server_send_error(client, ERROR_BAD_COMMAND,
                              "Invalid command token");
            goto fail;
        }
        memcpy(&tmp, p, 4);
        arglen = ntohl(tmp);
        p += 4;
        if ((length - (p - buffer)) < arglen) {
            warn("command data invalid");
            server_send_error(client, ERROR_BAD_COMMAND,
                              "Invalid command token");
            goto fail;
        }
        argv[count] = xmalloc(sizeof(struct iovec));
        argv[count]->iov_len = arglen;
        if (arglen == 0)
            argv[count]->iov_base = NULL;
        else {
            argv[count]->iov_base = xmalloc(arglen);
            memcpy(argv[count]->iov_base, p, arglen);
        }
        count++;
        p += arglen;
        debug("arg %lu has length %lu", (unsigned long) count,
              (unsigned long) arglen);
    }
    if (count != argc || p != buffer + length) {
        warn("argument count differs from arguments seen");
        server_send_error(client, ERROR_BAD_COMMAND, "Invalid command token");
        goto fail;
    }
    argv[count] = NULL;
    return argv;

fail:
    if (argv != NULL)
        server_free_command(argv);
    return NULL;
}


/*
 * Send an error back to the client.  Takes the client struct, the error code,
 * and the message to send and dispatches to the appropriate protocol-specific
 * function.  Returns true on success, false on failure.
 */
bool
server_send_error(struct client *client, enum error_codes error,
                  const char *message)
{
    if (client->protocol > 1)
        return server_v2_send_error(client, error, message);
    else {
        if (client->output != NULL)
            free(client->output);
        client->output = xmalloc(strlen(message) + 1);
        memcpy(client->output, message, strlen(message));
        client->output[strlen(message)] = '\n';
        client->outlen = strlen(message) + 1;
        return server_v1_send_output(client, -1);
    }
}
