/*
 * Message and error reporting (fatal).
 *
 * Usage:
 *
 *     extern int cleanup(void);
 *     extern void log(int, const char *, va_list, int);
 *
 *     message_fatal_cleanup = cleanup;
 *     message_program_name = argv[0];
 *
 *     die("Something fatal happened at %lu", time);
 *     sysdie("open of %s failed", filename);
 *
 *     message_handlers_die(1, log);
 *     die("This now goes through our log function");
 *
 * die() implements message reporting through user-configurable handler
 * functions and then exits, normally with a status of 1.  sysdie() does the
 * same but appends a colon, a space, and the results of strerror(errno) to
 * the end of the message.  Both functions accept printf-style formatting
 * strings and arguments.
 *
 * If message_fatal_cleanup is non-NULL, it is called before exit by die and
 * sysdie and its return value is used as the argument to exit.  It is a
 * pointer to a function taking no arguments and returning an int, and can be
 * used to call cleanup functions or to exit in some alternate fashion (such
 * as by calling _exit).
 *
 * If message_program_name is non-NULL, the string it points to, followed by a
 * colon and a space, is prepended to all error messages logged through the
 * message_log_stderr message handler (the default for die).
 *
 * Honoring error_program_name and printing to stderr is just the default
 * handler; with message_handlers_die the handler for die() can be changed.
 * By default, die prints to stderr.  message_handlers_die takes a count of
 * handlers and then that many function pointers, each one to a function that
 * takes a message length (the number of characters snprintf generates given
 * the format and arguments), a format, an argument list as a va_list, and the
 * applicable errno value (if any).
 *
 * This file is separate from messages.c so that the potentially fatal
 * functions aren't linked with code that will never call exit().  This helps
 * automated analysis ensure that shared libraries don't call exit().
 *
 * Copyright 2009 Russ Allbery <rra@stanford.edu>
 * Copyright 2008 Board of Trustees, Leland Stanford Jr. University
 * Copyright (c) 2004, 2005, 2006
 *     by Internet Systems Consortium, Inc. ("ISC")
 * Copyright (c) 1991, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001,
 *     2002, 2003 by The Internet Software Consortium and Rich Salz
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>

#include <errno.h>

#include <util/util.h>

/* The default message handler. */
static message_handler_func stderr_handlers[2] = {
    message_log_stderr, NULL
};
static message_handler_func *die_handlers = stderr_handlers;

/* If non-NULL, called before exit and its return value passed to exit. */
int (*message_fatal_cleanup)(void) = NULL;


/*
 * Set the handlers for die.  This duplicates code from messages.c but seems
 * to be the best way to handle separating the potentially fatal functions
 * from the rest.
 */
void
message_handlers_die(int count, ...)
{
    va_list args;
    int i;

    va_start(args, count);
    if (die_handlers != stderr_handlers)
        free(die_handlers);
    die_handlers = xmalloc(sizeof(message_handler_func) * (count + 1));
    for (i = 0; i < count; i++)
        die_handlers[i] = va_arg(args, message_handler_func);
    die_handlers[count] = NULL;
    va_end(args);
}


/*
 * The error reporting functions.  There is code duplication between the two
 * functions that could be avoided with judicious use of va_copy(), but it's
 * never seemed worth the effort.
 */
void
die(const char *format, ...)
{
    va_list args;
    message_handler_func *log;
    int length;

    va_start(args, format);
    length = vsnprintf(NULL, 0, format, args);
    va_end(args);
    if (length >= 0)
        for (log = die_handlers; *log != NULL; log++) {
            va_start(args, format);
            (**log)(length, format, args, 0);
            va_end(args);
        }
    exit(message_fatal_cleanup ? (*message_fatal_cleanup)() : 1);
}

void
sysdie(const char *format, ...)
{
    va_list args;
    message_handler_func *log;
    int length;
    int error = errno;

    va_start(args, format);
    length = vsnprintf(NULL, 0, format, args);
    va_end(args);
    if (length >= 0)
        for (log = die_handlers; *log != NULL; log++) {
            va_start(args, format);
            (**log)(length, format, args, error);
            va_end(args);
        }
    exit(message_fatal_cleanup ? (*message_fatal_cleanup)() : 1);
}
