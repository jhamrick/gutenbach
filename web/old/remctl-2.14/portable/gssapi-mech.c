/*
 * Define the Kerberos v5 GSS-API mechanism OID.
 *
 * This short bit of code exposes the Kerberos v5 GSS-API mechanism OID has
 * gss_mech_krb5 on platforms that don't have GSS_KRB5_MECHANISM or
 * gss_mech_krb5, such as Solaris 10.
 *
 * On Solaris 10, we could call gss_str_to_oid to convert "kerberos_v5" to an
 * OID or to parse the numeric form of an OID, but this doesn't rely on
 * configuration files and is just as portable in practice.
 */

#include <portable/gssapi.h>

#if !HAVE_DECL_GSS_MECH_KRB5
static const gss_OID_desc gss_mech_krb5_desc
    = { 9, "\052\206\110\206\367\022\001\002\002" };
const gss_OID_desc * const gss_mech_krb5 = &gss_mech_krb5_desc;
#endif
