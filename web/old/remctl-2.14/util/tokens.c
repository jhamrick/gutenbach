/*
 * Token handling routines.
 *
 * Low-level routines to send and receive remctl tokens.  token_send and
 * token_recv do not do anything to their provided input or output except
 * wrapping flags and a length around them.
 *
 * Originally written by Anton Ushakov
 * Extensive modifications by Russ Allbery <rra@stanford.edu>
 * Copyright 2002, 2003, 2004, 2005, 2006, 2007, 2008
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/gssapi.h>
#include <portable/socket.h>

#include <errno.h>

#include <util/util.h>

/*
 * Windows requires a different function when sending to sockets, but can't
 * return short writes on blocking sockets.
 */
#ifdef _WIN32
# define socket_xwrite(fd, b, s)        send((fd), (b), (s), 0)
#else
# define socket_xwrite(fd, b, s)        xwrite((fd), (b), (s))
#endif


/*
 * Equivalent to read, but reads all the available data up to the buffer
 * length, using multiple reads if needed and handling EINTR and EAGAIN.
 */
static ssize_t
xread(int fd, void *buffer, size_t size)
{
    size_t total;
    ssize_t status;
    int count = 0;

    if (size == 0)
        return 0;

    /* Abort the read if we try 100 times with no forward progress. */
    for (total = 0; total < size; total += status) {
        if (++count > 100)
            break;
        status = socket_read(fd, (char *) buffer + total, size - total);
        if (status > 0)
            count = 0;
        if (status < 0) {
            if ((errno != EINTR) && (errno != EAGAIN))
                break;
            status = 0;
        }
    }
    return (status < 0) ? status : (ssize_t) total;
}


/*
 * Send a token to a file descriptor.  Takes the file descriptor, the token,
 * and the flags (a single byte, even though they're passed in as an integer)
 * and writes them to the file descriptor.  Returns TOKEN_OK on success and
 * TOKEN_FAIL_SYSTEM or TOKEN_FAIL_SOCKET on an error (including partial
 * writes).
 */
enum token_status
token_send(int fd, int flags, gss_buffer_t tok)
{
    ssize_t status;
    size_t buflen;
    char *buffer;
    unsigned char char_flags = (unsigned char) flags;
    OM_uint32 len = htonl(tok->length);

    /* Send out the whole message in a single write. */
    buflen = 1 + sizeof(OM_uint32) + tok->length;
    buffer = malloc(buflen);
    if (buffer == NULL)
        return TOKEN_FAIL_SYSTEM;
    memcpy(buffer, &char_flags, 1);
    memcpy(buffer + 1, &len, sizeof(OM_uint32));
    memcpy(buffer + 1 + sizeof(OM_uint32), tok->value, tok->length);
    status = socket_xwrite(fd, buffer, buflen);
    free(buffer);
    if (status < 0 || (size_t) status != buflen)
        return TOKEN_FAIL_SOCKET;
    else
        return TOKEN_OK;
}


/*
 * Receive a token from a file descriptor.  Takes the file descriptor, a
 * buffer into which to store the token, a pointer into which to store the
 * flags, and the maximum token length we're willing to accept.  Returns
 * TOKEN_OK on success.  On failure, returns one of:
 *
 *     TOKEN_FAIL_SYSTEM       System call failed, errno set.
 *     TOKEN_FAIL_SOCKET       Socket call failed, socket_errno set.
 *     TOKEN_FAIL_INVALID      Invalid token format.
 *     TOKEN_FAIL_LARGE        Token data larger than provided limit.
 *     TOKEN_FAIL_EOF          Unexpected end of file
 *
 * TOKEN_FAIL_SYSTEM and TOKEN_FAIL_SOCKET are the same on UNIX but different
 * on Windows.
 *
 * recv_token reads the token flags (a single byte, even though they're stored
 * into an integer, then reads the token length (as a network long), allocates
 * memory to hold the data, and then reads the token data from the file
 * descriptor.  It blocks to read the length and data, if necessary.  On a
 * successful return, the value member of the token should be freed with
 * free().
 */
enum token_status
token_recv(int fd, int *flags, gss_buffer_t tok, size_t max)
{
    ssize_t status;
    OM_uint32 len;
    unsigned char char_flags;

    status = xread(fd, &char_flags, 1);
    if (status < 0)
        return TOKEN_FAIL_SOCKET;
    else if (status == 0)
        return TOKEN_FAIL_EOF;
    *flags = char_flags;

    status = xread(fd, &len, sizeof(OM_uint32));
    if (status < 0)
        return TOKEN_FAIL_SOCKET;
    else if (status == 0)
        return TOKEN_FAIL_EOF;
    else if (status != sizeof(OM_uint32))
        return TOKEN_FAIL_INVALID;
    tok->length = ntohl(len);
    if (tok->length > max)
        return TOKEN_FAIL_LARGE;

    tok->value = malloc(tok->length);
    if (tok->value == NULL)
        return TOKEN_FAIL_SYSTEM;
    status = xread(fd, tok->value, tok->length);
    if (status < 0) {
        free(tok->value);
        return TOKEN_FAIL_SOCKET;
    } else if (status != (ssize_t) tok->length) {
        free(tok->value);
        return TOKEN_FAIL_INVALID;
    }
    return TOKEN_OK;
}
