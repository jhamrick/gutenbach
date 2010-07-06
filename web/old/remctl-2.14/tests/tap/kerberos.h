/*
 * Utility functions for tests that use Kerberos.
 *
 * Copyright 2006, 2007, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#ifndef TAP_KERBEROS_H
#define TAP_KERBEROS_H 1

#include <config.h>
#include <portable/macros.h>

BEGIN_DECLS

/*
 * Set up Kerberos, returning the test principal in newly allocated memory if
 * we were successful.  If there is no principal in tests/data/test.principal
 * or no keytab in tests/data/test.keytab, return NULL.  Otherwise, on
 * failure, calls bail().
 */
char *kerberos_setup(void);

/* Clean up at the end of a test. */
void kerberos_cleanup(void);

END_DECLS

#endif /* !TAP_MESSAGES_H */
