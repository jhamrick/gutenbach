/*
 * Error handling for the remctl client library.
 *
 * A set of helper routines to do error handling inside the remctl client
 * library.  These mostly involve setting the error parameter in the remctl
 * struct to something appropriate so that the next call to remctl_error will
 * return the appropriate details.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2006, 2007, 2008
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/gssapi.h>
#include <portable/socket.h>

#include <errno.h>

#include <client/internal.h>
#include <util/util.h>

/*
 * Internal function to set the error message, freeing an old error message if
 * one is present.
*/
void
internal_set_error(struct remctl *r, const char *format, ...)
{
    va_list args;
    int status;

    if (r->error != NULL)
        free(r->error);
    va_start(args, format);
    status = vasprintf(&r->error, format, args);
    va_end(args);

    /*
     * If vasprintf fails, there isn't much we can do, but make sure that at
     * least the error is in a consistent state.
     */
    if (status < 0)
        r->error = NULL;
}


/*
 * Internal function to set the remctl error message from a GSS-API error
 * message.
 */
void
internal_gssapi_error(struct remctl *r, const char *error, OM_uint32 major,
                      OM_uint32 minor)
{
    if (r->error != NULL)
        free(r->error);
    r->error = gssapi_error_string(error, major, minor);
}


/*
 * Internal function to set the remctl error message from a token error.
 * Handles the various token failure codes from the token_send and token_recv
 * functions and their *_priv counterparts.
 */
void
internal_token_error(struct remctl *r, const char *error, int status,
                     OM_uint32 major, OM_uint32 minor)
{
    switch (status) {
    case TOKEN_OK:
        internal_set_error(r, "error %s", error);
        break;
    case TOKEN_FAIL_SYSTEM:
        internal_set_error(r, "error %s: %s", error, strerror(errno));
        break;
    case TOKEN_FAIL_SOCKET:
        internal_set_error(r, "error %s: %s", error,
                           socket_strerror(socket_errno));
        break;
    case TOKEN_FAIL_INVALID:
        internal_set_error(r, "error %s: invalid token format", error);
        break;
    case TOKEN_FAIL_LARGE:
        internal_set_error(r, "error %s: token too larger", error);
        break;
    case TOKEN_FAIL_EOF:
        internal_set_error(r, "error %s: unexpected end of file", error);
        break;
    case TOKEN_FAIL_GSSAPI:
        internal_gssapi_error(r, error, major, minor);
        break;
    default:
        internal_set_error(r, "error %s: unknown error", error);
        break;
    }
}
