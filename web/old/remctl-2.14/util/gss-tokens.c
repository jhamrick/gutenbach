/*
 * GSS token handling routines.
 *
 * Higher-level wrappers around the low-level token handling routines that
 * apply integrity and privacy protection to the token data before sending.
 * token_send_priv and token_recv_priv are similar to token_send and
 * token_recv except that they also take a GSS-API context and a GSS-API major
 * and minor status to report errors.
 *
 * Originally written by Anton Ushakov
 * Extensive modifications by Russ Allbery <rra@stanford.edu>
 * Copyright 2002, 2003, 2004, 2005, 2006, 2007, 2008
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See README for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/gssapi.h>

#include <util/util.h>

/*
 * If we're running the test suite, call testing versions of the token
 * functions.
 */
#if TESTING
# define token_send fake_token_send
# define token_recv fake_token_recv
enum token_status token_send(int, int, gss_buffer_t);
enum token_status token_recv(int, int *, gss_buffer_t, size_t);
#endif


/*
 * Wraps, encrypts, and sends a data payload token.  Takes the file descriptor
 * to send to, the GSS-API context, the flags to send with the token, the
 * token, and the status variables.  Returns TOKEN_OK on success and
 * TOKEN_FAIL_SYSTEM or TOKEN_FAIL_GSSAPI on failure.  If the latter is
 * returned, the major and minor status variables will be set to something
 * useful.
 *
 * As a hack to support remctl v1, look to see if the flags includes
 * TOKEN_SEND_MIC and don't include TOKEN_PROTOCOL.  If so, expect the remote
 * side to reply with a MIC, which we then verify.
*/
enum token_status
token_send_priv(int fd, gss_ctx_id_t ctx, int flags, gss_buffer_t tok,
                OM_uint32 *major, OM_uint32 *minor)
{
    gss_buffer_desc out, mic;
    int state, micflags;
    enum token_status status;

    if (tok->length > TOKEN_MAX_DATA)
        return TOKEN_FAIL_LARGE;
    *major = gss_wrap(minor, ctx, 1, GSS_C_QOP_DEFAULT, tok, &state, &out);
    if (*major != GSS_S_COMPLETE)
        return TOKEN_FAIL_GSSAPI;
    status = token_send(fd, flags, &out);
    gss_release_buffer(minor, &out);
    if (status != TOKEN_OK)
        return status;
    if ((flags & TOKEN_SEND_MIC) && !(flags & TOKEN_PROTOCOL)) {
        status = token_recv(fd, &micflags, &mic, 10 * 1024);
        if (status != TOKEN_OK)
            return status;
        if (micflags != TOKEN_MIC) {
            gss_release_buffer(minor, &mic);
            return TOKEN_FAIL_INVALID;
        }
        *major = gss_verify_mic(minor, ctx, tok, &mic, NULL);
        if (*major != GSS_S_COMPLETE) {
            gss_release_buffer(minor, &mic);
            return TOKEN_FAIL_GSSAPI;
        }
        gss_release_buffer(minor, &mic);
    }
    return TOKEN_OK;
}


/*
 * Receives and unwraps a data payload token.  Takes the file descriptor,
 * GSS-API context, a pointer into which to storge the flags, a buffer for the
 * message, and a place to put GSS-API major and minor status.  Returns
 * TOKEN_OK on success or one of the TOKEN_FAIL_* statuses on failure.  On
 * success, tok will contain newly allocated memory and should be freed when
 * no longer needed using gss_release_buffer.  On failure, any allocated
 * memory will be freed.
 *
 * As a hack to support remctl v1, look to see if the flags includes
 * TOKEN_SEND_MIC and do not include TOKEN_PROTOCOL.  If so, calculate a MIC
 * and send it back.
 */
enum token_status
token_recv_priv(int fd, gss_ctx_id_t ctx, int *flags, gss_buffer_t tok,
                size_t max, OM_uint32 *major, OM_uint32 *minor)
{
    gss_buffer_desc in, mic;
    int state;
    enum token_status status;

    status = token_recv(fd, flags, &in, max);
    if (status != TOKEN_OK)
        return status;
    *major = gss_unwrap(minor, ctx, &in, tok, &state, NULL);
    free(in.value);
    if (*major != GSS_S_COMPLETE)
        return TOKEN_FAIL_GSSAPI;
    if ((*flags & TOKEN_SEND_MIC) && !(*flags & TOKEN_PROTOCOL)) {
        *major = gss_get_mic(minor, ctx, GSS_C_QOP_DEFAULT, tok, &mic);
        if (*major != GSS_S_COMPLETE) {
            gss_release_buffer(minor, tok);
            return TOKEN_FAIL_GSSAPI;
        }
        status = token_send(fd, TOKEN_MIC, &mic);
        if (status != TOKEN_OK) {
            gss_release_buffer(minor, tok);
            gss_release_buffer(minor, &mic);
            return status;
        }
        gss_release_buffer(minor, &mic);
        *flags = (*flags) & ~TOKEN_SEND_MIC;
    }
    return TOKEN_OK;
}
