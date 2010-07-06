/*
 * Public interface to remctl client library.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Based on prior work by Anton Ushakov
 * Copyright 2002, 2003, 2004, 2005, 2006, 2007, 2008
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * Permission to use, copy, modify, and distribute this software and its
 * documentation for any purpose and without fee is hereby granted, provided
 * that the above copyright notice appear in all copies and that both that
 * copyright notice and this permission notice appear in supporting
 * documentation, and that the name of Stanford University not be used in
 * advertising or publicity pertaining to distribution of the software without
 * specific, written prior permission.  Stanford University makes no
 * representations about the suitability of this software for any purpose.  It
 * is provided "as is" without express or implied warranty.
 *
 * THIS SOFTWARE IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
 */

#ifndef REMCTL_H
#define REMCTL_H 1

#include <sys/types.h>          /* size_t */

/*
 * Normally we treat this as an opaque struct and clients who want to use the
 * iovec interface need to include <sys/uio.h> themselves.  However, Windows
 * doesn't provide this struct, so we define it for Windows.  It will already
 * be defined by remctl's internal build system, so deal with that.
 */
#if defined(_WIN32) && !defined(PORTABLE_UIO_H)
struct iovec {
    void *iov_base;
    size_t iov_len;
};
#else
struct iovec;
#endif

/*
 * BEGIN_DECLS is used at the beginning of declarations so that C++
 * compilers don't mangle their names.  END_DECLS is used at the end.
 */
#undef BEGIN_DECLS
#undef END_DECLS
#ifdef __cplusplus
# define BEGIN_DECLS    extern "C" {
# define END_DECLS      }
#else
# define BEGIN_DECLS    /* empty */
# define END_DECLS      /* empty */
#endif

/* The standard remctl port and the legacy port used before 2.11. */
#define REMCTL_PORT     4373
#define REMCTL_PORT_OLD 4444

/* The standard remctl service name for /etc/services. */
#define REMCTL_SERVICE  "remctl"

/* Used to hold the return from a simple remctl call. */
struct remctl_result {
    char *error;                /* remctl error if non-NULL. */
    char *stdout_buf;           /* Standard output. */
    size_t stdout_len;          /* Length of standard output. */
    char *stderr_buf;           /* Standard error. */
    size_t stderr_len;          /* Length of standard error. */
    int status;                 /* Exit status of remote command. */
};

/* The type of a remctl_output struct. */
enum remctl_output_type {
    REMCTL_OUT_OUTPUT,
    REMCTL_OUT_STATUS,
    REMCTL_OUT_ERROR,
    REMCTL_OUT_DONE
};

/* Used to return incremental output from a persistant connection. */
struct remctl_output {
    enum remctl_output_type type;
    char *data;
    size_t length;
    int stream;                 /* 1 == stdout, 2 == stderr */
    int status;                 /* Exit status of remote command. */
    int error;                  /* Remote error code. */
};

/* Opaque struct representing an open remctl connection. */
struct remctl;

BEGIN_DECLS

/*
 * First, the simple interface.  Given a host, a port (may be 0 to use
 * REMCTL_PORT with fallback to REMCTL_PORT_OLD), the principal to
 * authenticate as (may be NULL to use host/<host>), and a command (as a
 * null-terminated argv-style vector), run the command on that host and port
 * and return a struct remctl_result.  The result should be freed with
 * remctl_result_free.
 */
struct remctl_result *remctl(const char *host, unsigned short port,
                             const char *principal, const char **command);
void remctl_result_free(struct remctl_result *);

/*
 * Now, the more complex persistant interface.  The basic housekeeping
 * functions.  port may be 0, in which case REMCTL_PORT is used with fallback
 * to REMCTL_PORT_OLD.  principal may be NULL, in which case host/<host> is
 * used (with no transformations applied to host at all).
 */
struct remctl *remctl_new(void);
int remctl_open(struct remctl *, const char *host, unsigned short port,
                const char *principal);
void remctl_close(struct remctl *);

/*
 * Send a complete remote command.  Returns true on success, false on failure.
 * On failure, use remctl_error to get the error.  There are two forms of this
 * function; remctl_command takes a NULL-terminated array of nul-terminated
 * strings and remctl_commandv takes an array of struct iovecs of length
 * count.  The latter form should be used for binary data.
 */
int remctl_command(struct remctl *, const char **command);
int remctl_commandv(struct remctl *, const struct iovec *, size_t count);

/*
 * Retrieve output from the remote server.  Each call to this function on the
 * same connection invalidates the previous returned remctl_output struct, so
 * copy any data that should be persistant before calling this function again.
 *
 * This function will return zero or more REMCTL_OUT_OUTPUT types followed by
 * a REMCTL_OUT_STATUS type, *or* a REMCTL_OUT_ERROR type.  In either case,
 * any subsequent call before sending a new command will return
 * REMCTL_OUT_DONE.  If the function returns NULL, an internal error occurred;
 * call remctl_error to retrieve the error message.
 *
 * The remctl_output struct should *not* be freed by the caller.  It will be
 * invalidated after another call to remctl_output or to remctl_close on the
 * same connection.
 */
struct remctl_output *remctl_output(struct remctl *);

/*
 * Call remctl_error after an error return to retrieve the internal error
 * message.  The returned error string will be invalidated by any subsequent
 * call to a remctl library function.
 */
const char *remctl_error(struct remctl *);

END_DECLS

#endif /* !REMCTL_H */
