/*
 * Utility functions to test message handling.
 *
 * These functions set up a message handler to trap warn and notice output
 * into a buffer that can be inspected later, allowing testing of error
 * handling.
 *
 * Copyright 2006, 2007, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 * Copyright (c) 2004, 2005, 2006
 *     by Internet Systems Consortium, Inc. ("ISC")
 * Copyright (c) 1991, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001,
 *     2002, 2003 by The Internet Software Consortium and Rich Salz
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>

#include <tests/tap/messages.h>
#include <util/util.h>

/* A global buffer into which message_log_buffer stores error messages. */
char *errors = NULL;


/*
 * An error handler that appends all errors to the errors global.  Used by
 * error_capture.
 */
static void
message_log_buffer(int len, const char *fmt, va_list args, int error UNUSED)
{
    char *message;

    message = xmalloc(len + 1);
    vsnprintf(message, len + 1, fmt, args);
    if (errors == NULL) {
        errors = concat(message, "\n", (char *) 0);
    } else {
        char *new_errors;

        new_errors = concat(errors, message, "\n", (char *) 0);
        free(errors);
        errors = new_errors;
    }
    free(message);
}


/*
 * Turn on the capturing of errors.  Errors will be stored in the global
 * errors variable where they can be checked by the test suite.  Capturing is
 * turned off with errors_uncapture.
 */
void
errors_capture(void)
{
    if (errors != NULL) {
        free(errors);
        errors = NULL;
    }
    message_handlers_warn(1, message_log_buffer);
    message_handlers_notice(1, message_log_buffer);
}


/*
 * Turn off the capturing of errors again.
 */
void
errors_uncapture(void)
{
    message_handlers_warn(1, message_log_stderr);
    message_handlers_notice(1, message_log_stdout);
}
