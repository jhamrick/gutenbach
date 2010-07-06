/*
 * Utility functions for tests that use remctl.
 *
 * Provides functions to start and stop a remctl daemon that uses the test
 * Kerberos environment and runs on port 14373 instead of the default 4373.
 *
 * Copyright 2006, 2007, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#ifndef TAP_REMCTL_H
#define TAP_REMCTL_H 1

#include <config.h>
#include <portable/macros.h>

#include <sys/types.h>          /* pid_t */

BEGIN_DECLS

/*
 * Start and stop remctld for tests that use it.  kerberos_setup() should
 * normally be called first to check whether a Kerberos configuration is
 * available and to set KRB5_KTNAME.  Takes the path to remctld, which may be
 * found via configure, the principal (returned by kerberos_setup), and the
 * path to the configuration file.
 */
pid_t remctld_start(const char *path, const char *principal,
                    const char *config);
void remctld_stop(pid_t);

END_DECLS

#endif /* !TAP_REMCTL_H */
