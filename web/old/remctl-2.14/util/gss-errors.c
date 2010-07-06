/*
 * Shared GSS-API error handling code.
 *
 * Helper functions to interpret GSS-API errors that can be shared between the
 * client and the server.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2007 Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/gssapi.h>

#include <util/util.h>


/*
 * Turn a GSS-API error code pair into a human-readable string, prefixed with
 * "GSS-API error" and the provided string.  Uses gss_display_status to get
 * the internal error message.  Returns a newly allocated string that the
 * caller must free.
 */
char *
gssapi_error_string(const char *prefix, OM_uint32 major, OM_uint32 minor)
{
    char *string, *old;
    gss_buffer_desc msg;
    OM_uint32 msg_ctx, status;

    string = NULL;
    msg_ctx = 0;
    do {
        gss_display_status(&status, major, GSS_C_GSS_CODE,
                           (const gss_OID) GSS_KRB5_MECHANISM,
                           &msg_ctx, &msg);
        if (string != NULL) {
            old = string;
            string = concat(string, ", ", msg.value, (char *) 0);
            free(old);
        } else {
            string = concat("GSS-API error ", prefix, ": ", msg.value,
                            (char *) 0);
        }
    } while (msg_ctx != 0);
    if (minor != 0) {
        msg_ctx = 0;
        do {
            gss_display_status(&status, minor, GSS_C_MECH_CODE,
                               (const gss_OID) GSS_KRB5_MECHANISM, &msg_ctx,
                               &msg);
            old = string;
            string = concat(string, ", ", msg.value, (char *) 0);
            free(old);
        } while (msg_ctx != 0);
    }
    return string;
}
