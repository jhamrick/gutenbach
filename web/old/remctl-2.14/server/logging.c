/*
 * Logging and error handling for the remctld server.
 *
 * A set of helper routines to do error handling and other logging for
 * remctld, mostly wrappers around warn and die which will send errors to the
 * right place.
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
#include <portable/uio.h>

#include <errno.h>

#include <server/internal.h>
#include <util/util.h>

/*
 * Report a GSS-API failure using warn.
 */
void
warn_gssapi(const char *error, OM_uint32 major, OM_uint32 minor)
{
    char *string;

    string = gssapi_error_string(error, major, minor);
    warn("%s", string);
    free(string);
}


/*
 * Report a token error using warn.
 */
void
warn_token(const char *error, int status, OM_uint32 major, OM_uint32 minor)
{
    switch (status) {
    case TOKEN_OK:
        warn("error %s", error);
        break;
    case TOKEN_FAIL_SYSTEM:
        syswarn("error %s", error);
        break;
    case TOKEN_FAIL_SOCKET:
        warn("error %s: %s", error, socket_strerror(socket_errno));
        break;
    case TOKEN_FAIL_INVALID:
        warn("error %s: invalid token format", error);
        break;
    case TOKEN_FAIL_LARGE:
        warn("error %s: token too large", error);
        break;
    case TOKEN_FAIL_EOF:
        warn("error %s: unexpected end of file", error);
        break;
    case TOKEN_FAIL_GSSAPI:
        warn_gssapi(error, major, minor);
        break;
    default:
        warn("error %s: unknown error", error);
        break;
    }
}


/*
 * Log a command.  Takes the argument vector, the configuration line that
 * matched the command, and the principal running the command.
 */
void
server_log_command(struct iovec **argv, struct confline *cline,
                   const char *user)
{
    char *command, *p;
    unsigned int i;
    unsigned int *j;
    struct vector *masked;
    const char *arg;

    masked = vector_new();
    for (i = 0; argv[i] != NULL; i++) {
        arg = NULL;
        if (cline != NULL) {
            if (cline->logmask != NULL)
                for (j = cline->logmask; *j != 0; j++) {
                    if (*j == i) {
                        arg = "**MASKED**";
                        break;
                    }
                }
            if (i > 0
                && (cline->stdin_arg == (long) i
                    || (cline->stdin_arg == -1 && argv[i + 1] == NULL))) {
                arg = "**DATA**";
            }
        }
        if (arg != NULL)
            vector_add(masked, arg);
        else
            vector_addn(masked, argv[i]->iov_base, argv[i]->iov_len);
    }
    command = vector_join(masked, " ");
    vector_free(masked);

    /* Replace non-printable characters with . when logging. */
    for (p = command; *p != '\0'; p++)
        if (*p < 9 || (*p > 9 && *p < 32) || *p == 127)
            *p = '.';
    notice("COMMAND from %s: %s", user, command);
    free(command);
}
