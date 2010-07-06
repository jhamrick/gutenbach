/*
 * Protocol v1, client implementation.
 *
 * This is the client implementation of the old v1 protocol, which doesn't
 * support streaming, keep-alive, or many of the other features of the current
 * protocol.  We shoehorn this protocol into the same API as the new protocol
 * so that clients don't have to care, but some functions (like continued
 * commands) will return unimplemented errors.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Based on work by Anton Ushakov
 * Copyright 2002, 2003, 2004, 2005, 2006, 2007, 2008
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/gssapi.h>
#include <portable/socket.h>
#include <portable/uio.h>

#include <errno.h>

#include <client/internal.h>
#include <client/remctl.h>
#include <util/util.h>


/*
 * Send a command to the server using protocol v1.  Returns true on success,
 * false on failure.
 */
bool
internal_v1_commandv(struct remctl *r, const struct iovec *command,
                     size_t count)
{
    gss_buffer_desc token;
    size_t i;
    char *p;
    OM_uint32 data, major, minor;
    int status;

    /* Allocate room for the total message: argc, {<length><arg>}+. */
    token.length = 4;
    for (i = 0; i < count; i++)
        token.length += 4 + command[i].iov_len;
    token.value = malloc(token.length);
    if (token.value == NULL) {
        internal_set_error(r, "cannot allocate memory: %s", strerror(errno));
        return false;
    }

    /* First, the argument count.  Then, each argument. */
    p = token.value;
    data = htonl(count);
    memcpy(p, &data, 4);
    p += 4;
    for (i = 0; i < count; i++) {
        data = htonl(command[i].iov_len);
        memcpy(p, &data, 4);
        p += 4;
        memcpy(p, command[i].iov_base, command[i].iov_len);
        p += command[i].iov_len;
    }

    /* Send the result. */
    status = token_send_priv(r->fd, r->context, TOKEN_DATA | TOKEN_SEND_MIC,
                             &token, &major, &minor);
    if (status != TOKEN_OK) {
        internal_token_error(r, "sending token", status, major, minor);
        free(token.value);
        return false;
    }
    free(token.value);
    r->ready = true;
    return true;
}


/*
 * Retrieve the output from the server using protocol version one and return
 * it.  This function will actually be called twice, once to retrieve the
 * output data and once to retrieve the exit status.  The old protocol
 * returned those together in one message, so we have to buffer the exit
 * status and return it on the second call.  Returns a remctl output struct on
 * success and NULL on failure.
 */
struct remctl_output *
internal_v1_output(struct remctl *r)
{
    int status, flags;
    gss_buffer_desc token;
    OM_uint32 data, major, minor, length;
    char *p;

    /*
     * First, see if we already had an output struct.  If so, this is the
     * second call and we should just return the exit status.
     */
    if (r->output != NULL && !r->ready) {
        if (r->output->type == REMCTL_OUT_STATUS)
            r->output->type = REMCTL_OUT_DONE;
        else {
            internal_output_wipe(r->output);
            r->output->type = REMCTL_OUT_STATUS;
        }
        r->output->status = r->status;
        return r->output;
    }

    /* Otherwise, we have to read the token from the server. */
    status = token_recv_priv(r->fd, r->context, &flags, &token,
                             TOKEN_MAX_LENGTH, &major, &minor);
    if (status != TOKEN_OK) {
        internal_token_error(r, "receiving token", status, major, minor);
        if (status == TOKEN_FAIL_EOF) {
            socket_close(r->fd);
            r->fd = -1;
        }
        return NULL;
    }
    if (flags != TOKEN_DATA) {
        internal_set_error(r, "unexpected token from server");
        gss_release_buffer(&minor, &token);
        return NULL;
    }

    /* Extract the return code, message length, and data. */
    if (token.length < 8) {
        internal_set_error(r, "malformed result token from server");
        gss_release_buffer(&minor, &token);
        return NULL;
    }
    p = token.value;
    memcpy(&data, p, 4);
    r->status = ntohl(data);
    p += 4;
    memcpy(&data, p, 4);
    length = ntohl(data);
    p += 4;
    if (length != token.length - 8) {
        internal_set_error(r, "malformed result token from server");
        gss_release_buffer(&minor, &token);
        return NULL;
    }

    /*
     * Allocate the new output token.  We make another copy of the data,
     * unfortunately, so that we don't have to keep the token around to free
     * later.
     */
    r->output = malloc(sizeof(struct remctl_output));
    if (r->output == NULL) {
        internal_set_error(r, "cannot allocate memory: %s", strerror(errno));
        gss_release_buffer(&minor, &token);
        return NULL;
    }
    r->output->type = REMCTL_OUT_OUTPUT;
    r->output->data = malloc(length);
    if (r->output->data == NULL) {
        internal_set_error(r, "cannot allocate memory: %s", strerror(errno));
        gss_release_buffer(&minor, &token);
        return NULL;
    }
    memcpy(r->output->data, p, length);
    r->output->length = length;
    gss_release_buffer(&minor, &token);

    /*
     * We always claim everything was stdout since we have no way of knowing
     * better with protocol version one.
     */
    r->output->stream = 1;

    /*
     * We can only do one round with protocol version one, so close the
     * connection now.
     */
    socket_close(r->fd);
    r->fd = -1;
    r->ready = false;
    return r->output;
}
