/*
 * Protocol v2, client implementation.
 *
 * This is the client implementation of the new v2 protocol.  It's fairly
 * close to the regular remctl API.
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
 * Send a command to the server using protocol v2.  Returns true on success,
 * false on failure.
 *
 * All of the complexity in this function comes from implementing command
 * continuation.  The protocol specifies that commands can be continued by
 * tresting the command as one huge token, chopping it into as many pieces as
 * desired, and putting the MESSAGE_COMMAND header on each piece with the
 * appropriate continue status.  We don't take full advantage of that (we
 * don't, for instance, ever split numbers across token boundaries), but we do
 * use this to handle commands where all the data is longer than
 * TOKEN_MAX_DATA.
 */
bool
internal_v2_commandv(struct remctl *r, const struct iovec *command,
                     size_t count)
{
    size_t length, iov, offset, sent, left, delta;
    gss_buffer_desc token;
    char *p;
    OM_uint32 data, major, minor;
    int status;

    /* Determine the total length of the message. */
    length = 4;
    for (iov = 0; iov < count; iov++)
        length += 4 + command[iov].iov_len;

    /*
     * Now, loop until we've conveyed the entire message.  Each token we send
     * to the server must include the standard header and the continue status.
     * The first token then has the argument count, and the remainder of the
     * command consists of pairs of argument length and argument data.
     *
     * If the entire message length plus the overhead for the header is less
     * than TOKEN_MAX_DATA, we send it in one go.  Otherwise, each time
     * through this loop, we pull off as much data as we can.  We break the
     * tokens either in the middle of an argument or just before an argument
     * length; we never send part of the argument length number and we always
     * include at least one byte of the argument after the argument length.
     * The protocol is more lenient, but those constraints make bookkeeping
     * easier.
     *
     * iov is the index of the argument we're currently sending.  offset is
     * the amount of that argument data we've already sent.  sent holds the
     * total length sent so far so that we can tell when we're done.
     */
    iov = 0;
    offset = 0;
    sent = 0;
    while (sent < length) {
        if (length - sent > TOKEN_MAX_DATA - 4)
            token.length = TOKEN_MAX_DATA;
        else
            token.length = length - sent + 4;
        token.value = malloc(token.length);
        if (token.value == NULL) {
            internal_set_error(r, "cannot allocate memory: %s",
                               strerror(errno));
            return false;
        }
        left = token.length - 4;

        /* Each token begins with the protocol version and message type. */
        p = token.value;
        p[0] = 2;
        p[1] = MESSAGE_COMMAND;
        p += 2;

        /* Keep-alive flag.  Always set to true for now. */
        *p = 1;
        p++;

        /* Continue status. */
        if (token.length == length - sent + 4)
            *p = (sent == 0) ? 0 : 3;
        else
            *p = (sent == 0) ? 1 : 2;
        p++;

        /* Argument count if we haven't sent anything yet. */
        if (sent == 0) {
            data = htonl(count);
            memcpy(p, &data, 4);
            p += 4;
            sent += 4;
            left -= 4;
        }

        /*
         * Now, as many arguments as will fit.  If offset is 0, we're at the
         * beginning of an argument and need to send the length.  Make sure,
         * if we're at the beginning of an argument, that we can add at least
         * five octets to this token.  The length plus at least one octet must
         * fit (or just the length if that argument is zero-length).
         */
        for (; iov < count; iov++) {
            if (offset == 0) {
                if (left < 4 || (left < 5 && command[iov].iov_len > 0))
                    break;
                data = htonl(command[iov].iov_len);
                memcpy(p, &data, 4);
                p += 4;
                sent += 4;
                left -= 4;
            }
            if (left >= command[iov].iov_len - offset)
                delta = command[iov].iov_len - offset;
            else
                delta = left;
            memcpy(p, (char *) command[iov].iov_base + offset, delta);
            p += delta;
            sent += delta;
            offset += delta;
            left -= delta;
            if (offset < (size_t) command[iov].iov_len)
                break;
            offset = 0;
        }

        /* Send the result. */
        token.length -= left;
        status = token_send_priv(r->fd, r->context,
                                 TOKEN_DATA | TOKEN_PROTOCOL, &token,
                                 &major, &minor);
        if (status != TOKEN_OK) {
            internal_token_error(r, "sending token", status, major, minor);
            free(token.value);
            return false;
        }
        free(token.value);
    }
    r->ready = true;
    return true;
}


/*
 * Send a quit command to the server using protocol v2.  Returns true on
 * success, false on failure.
 */
bool
internal_v2_quit(struct remctl *r)
{
    gss_buffer_desc token;
    char buffer[2] = { 2, MESSAGE_QUIT };
    OM_uint32 major, minor;
    int status;

    token.length = 1 + 1;
    token.value = buffer;
    status = token_send_priv(r->fd, r->context, TOKEN_DATA | TOKEN_PROTOCOL,
                             &token, &major, &minor);
    if (status != TOKEN_OK) {
        internal_token_error(r, "sending token", status, major, minor);
        return false;
    }
    return true;
}


/*
 * Read a string from a server token, with its length starting at the given
 * offset, and store it in newly allocated memory in the remctl struct.
 * Returns true on success and false on any failure (also setting the error).
 */
static bool
internal_v2_read_string(struct remctl *r, gss_buffer_t token, size_t offset)
{
    size_t size;
    OM_uint32 data;
    const char *p;

    p = (const char *) token->value + offset;
    memcpy(&data, p, 4);
    p += 4;
    size = ntohl(data);
    if (size != token->length - (p - (char *) token->value)) {
        internal_set_error(r, "malformed result token from server");
        return false;
    }
    r->output->data = malloc(size);
    if (r->output->data == NULL) {
        internal_set_error(r, "cannot allocate memory: %s", strerror(errno));
        return false;
    }
    memcpy(r->output->data, p, size);
    r->output->length = size;
    return true;
}


/*
 * Retrieve the output from the server using protocol v2 and return it.  This
 * function may be called any number of times; if the last packet we got from
 * the server was a REMCTL_OUT_STATUS or REMCTL_OUT_ERROR, we'll return
 * REMCTL_OUT_DONE from that point forward.  Returns a remctl output struct on
 * success and NULL on failure.
 */
struct remctl_output *
internal_v2_output(struct remctl *r)
{
    int status, flags;
    gss_buffer_desc token;
    OM_uint32 data, major, minor;
    char *p;
    int type;

    /*
     * Initialize our output.  If we're not ready to read more data from the
     * server, return REMCTL_OUT_DONE.
     */
    if (r->output == NULL) {
        r->output = malloc(sizeof(struct remctl_output));
        if (r->output == NULL) {
            internal_set_error(r, "cannot allocate memory: %s",
                               strerror(errno));
            return NULL;
        }
        r->output->data = NULL;
    }
    internal_output_wipe(r->output);
    if (!r->ready)
        return r->output;

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
    if (flags != (TOKEN_DATA | TOKEN_PROTOCOL)) {
        internal_set_error(r, "unexpected token from server");
        goto fail;
    }
    if (token.length < 2) {
        internal_set_error(r, "malformed result token from server");
        goto fail;
    }

    /* Extract the message protocol and type. */
    p = token.value;
    if (p[0] != 2) {
        internal_set_error(r, "unexpected protocol %d from server", p[0]);
        goto fail;
    }
    type = p[1];

    /* Now, what we do depends on the message type. */
    switch (type) {
    case MESSAGE_OUTPUT:
        if (token.length < 2 + 5) {
            internal_set_error(r, "malformed result token from server");
            goto fail;
        }
        r->output->type = REMCTL_OUT_OUTPUT;
        if (p[2] != 1 && p[2] != 2) {
            internal_set_error(r, "unexpected stream %d from server", p[0]);
            goto fail;
        }
        r->output->stream = p[2];
        if (!internal_v2_read_string(r, &token, 3))
            goto fail;
        break;

    case MESSAGE_STATUS:
        if (token.length != 2 + 1) {
            internal_set_error(r, "malformed result token from server");
            goto fail;
        }
        r->output->type = REMCTL_OUT_STATUS;
        r->output->status = p[2];
        r->ready = 0;
        break;

    case MESSAGE_ERROR:
        if (token.length < 2 + 8) {
            internal_set_error(r, "malformed result token from server");
            goto fail;
        }
        r->output->type = REMCTL_OUT_ERROR;
        memcpy(&data, p + 2, 4);
        r->output->error = ntohl(data);
        if (!internal_v2_read_string(r, &token, 6))
            goto fail;
        r->ready = 0;
        break;

    default:
        internal_set_error(r, "unknown message type %d from server", type);
        goto fail;
    }

    /* We've finished analyzing the packet.  Return the results. */
    gss_release_buffer(&minor, &token);
    return r->output;

fail:
    gss_release_buffer(&minor, &token);
    return NULL;
}
