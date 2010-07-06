/*
 * Portability wrapper around <gssapi.h>.
 *
 * This header tries to encapsulate the differences between the MIT and
 * Heimdal GSS-API implementations and the differences between various
 * versions.
 */

#ifndef PORTABLE_GSSAPI_H
#define PORTABLE_GSSAPI_H 1

#include <config.h>

#ifdef HAVE_GSSAPI_H
# include <gssapi.h>
#else
# include <gssapi/gssapi.h>
#endif

/* Handle compatibility to older versions of MIT Kerberos. */
#ifndef HAVE_GSS_RFC_OIDS
# include <gssapi/gssapi_generic.h>
# define GSS_C_NT_USER_NAME gss_nt_user_name
# define GSS_C_NT_HOSTBASED_SERVICE gss_nt_service_name
#endif

/*
 * Heimdal provides a nice #define for this.  Sun, on the other hand,
 * provides no standard define at all, so configure has to add gssapi-mech.c
 * to the build and we declare the external symbol that will point to a
 * hard-coded GSS-API OID struct.
 */
#if !HAVE_DECL_GSS_KRB5_MECHANISM
# if HAVE_DECL_GSS_MECH_KRB5
#  include <gssapi/gssapi_krb5.h>
# else
extern const gss_OID_desc * const gss_mech_krb5;
# endif
# define GSS_KRB5_MECHANISM gss_mech_krb5
#endif

#endif /* PORTABLE_GSSAPI_H */
