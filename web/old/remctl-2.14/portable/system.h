/*
 * Standard system includes and portability adjustments.
 *
 * Declarations of routines and variables in the C library.  Including this
 * file is the equivalent of including all of the following headers,
 * portably:
 *
 *     #include <sys/types.h>
 *     #include <stdarg.h>
 *     #include <stdbool.h>
 *     #include <stdio.h>
 *     #include <stdlib.h>
 *     #include <stddef.h>
 *     #include <stdint.h>
 *     #include <string.h>
 *     #include <unistd.h>
 *
 * Missing functions are provided via #define or prototyped if available from
 * the util helper library.  Also provides some standard #defines.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * This work is hereby placed in the public domain by its author.
 */

#ifndef PORTABLE_SYSTEM_H
#define PORTABLE_SYSTEM_H 1

/* Make sure we have our configuration information. */
#include <config.h>

/* BEGIN_DECL and __attribute__. */
#include <portable/macros.h>

/* A set of standard ANSI C headers.  We don't care about pre-ANSI systems. */
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <string.h>
#if HAVE_INTTYPES_H
# include <inttypes.h>
#endif
#if HAVE_STDINT_H
# include <stdint.h>
#endif
#if HAVE_UNISTD_H
# include <unistd.h>
#endif

/* SCO OpenServer gets int32_t from here. */
#if HAVE_SYS_BITYPES_H
# include <sys/bitypes.h>
#endif

/* Get the bool type. */
#include <portable/stdbool.h>

BEGIN_DECLS

/*
 * Provide prototypes for functions not declared in system headers.  Use the
 * HAVE_DECL macros for those functions that may be prototyped but implemented
 * incorrectly or implemented without a prototype.
 */
#if !HAVE_ASPRINTF
extern int              asprintf(char **, const char *, ...)
    __attribute__((__visibility__("hidden")));
extern int              vasprintf(char **, const char *, va_list)
    __attribute__((__visibility__("hidden")));
#endif
#if !HAVE_DECL_SNPRINTF
extern int              snprintf(char *, size_t, const char *, ...)
    __attribute__((__format__(printf, 3, 4)));
#endif
#if !HAVE_DECL_VSNPRINTF
extern int              vsnprintf(char *, size_t, const char *, va_list);
#endif
#if !HAVE_DAEMON
extern int              daemon(int, int)
    __attribute__((__visibility__("hidden")));
#endif
#if !HAVE_SETENV
extern int              setenv(const char *, const char *, int)
    __attribute__((__visibility__("hidden")));
#endif
#if !HAVE_STRLCAT
extern size_t           strlcat(char *, const char *, size_t)
    __attribute__((__visibility__("hidden")));
#endif
#if !HAVE_STRLCPY
extern size_t           strlcpy(char *, const char *, size_t)
    __attribute__((__visibility__("hidden")));
#endif

END_DECLS

/* Windows provides snprintf under a different name. */
#ifdef _WIN32
# define snprintf _snprintf
#endif

/*
 * POSIX requires that these be defined in <unistd.h>.  If one of them has
 * been defined, all the rest almost certainly have.
 */
#ifndef STDIN_FILENO
# define STDIN_FILENO   0
# define STDOUT_FILENO  1
# define STDERR_FILENO  2
#endif

/*
 * C99 requires va_copy.  Older versions of GCC provide __va_copy.  Per the
 * Autoconf manual, memcpy is a generally portable fallback.
 */
#ifndef va_copy
# ifdef __va_copy
#  define va_copy(d, s)         __va_copy((d), (s))
# else
#  define va_copy(d, s)         memcpy(&(d), &(s), sizeof(va_list))
# endif
#endif

#endif /* !PORTABLE_SYSTEM_H */
