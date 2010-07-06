/*
 * Utility functions.
 *
 * This is a variety of utility functions that are used internally by pieces
 * of remctl.  Many of them came originally from INN.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Based on prior work by Anton Ushakov
 * Copyright 2002, 2003, 2004, 2005, 2006, 2007, 2008
 *     Board of Trustees, Leland Stanford Jr. University
 * Copyright (c) 2004, 2005, 2006, 2007
 *     by Internet Systems Consortium, Inc. ("ISC")
 * Copyright (c) 1991, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001,
 *     2002, 2003 by The Internet Software Consortium and Rich Salz
 *
 * See LICENSE for licensing terms.
 */

#ifndef UTIL_UTIL_H
#define UTIL_UTIL_H 1

#include <config.h>
#include <portable/gssapi.h>
#include <portable/macros.h>
#include <portable/stdbool.h>

#include <stdarg.h>
#include <sys/types.h>

/* Windows uses this for something else. */
#ifdef _WIN32
# undef ERROR_BAD_COMMAND
#endif

/* Used for unused parameters to silence gcc warnings. */
#define UNUSED __attribute__((__unused__))

BEGIN_DECLS

/* Forward declarations to avoid includes. */
struct addrinfo;
struct iovec;
struct sockaddr;

/* Maximum lengths from the protocol specification of tokens and data. */
#define TOKEN_MAX_LENGTH        (1024 * 1024)
#define TOKEN_MAX_DATA          (64 * 1024)

/* Failure return codes from token_send and token_recv. */
enum token_status {
    TOKEN_OK = 0,
    TOKEN_FAIL_SYSTEM  = -1,    /* System call failed, error in errno */
    TOKEN_FAIL_SOCKET  = -2,    /* Socket call failed, error in socket_errno */
    TOKEN_FAIL_INVALID = -3,    /* Invalid token from remote site */
    TOKEN_FAIL_LARGE   = -4,    /* Token data exceeds max length */
    TOKEN_FAIL_EOF     = -5,    /* Unexpected end of file while reading */
    TOKEN_FAIL_GSSAPI  = -6     /* GSS-API failure {en,de}crypting token */
};

/* Token types and flags. */
enum token_flags {
    TOKEN_NOOP          = (1 << 0),
    TOKEN_CONTEXT       = (1 << 1),
    TOKEN_DATA          = (1 << 2),
    TOKEN_MIC           = (1 << 3),
    TOKEN_CONTEXT_NEXT  = (1 << 4),
    TOKEN_SEND_MIC      = (1 << 5),
    TOKEN_PROTOCOL      = (1 << 6)
};

/* Message types. */
enum message_types {
    MESSAGE_COMMAND = 1,
    MESSAGE_QUIT    = 2,
    MESSAGE_OUTPUT  = 3,
    MESSAGE_STATUS  = 4,
    MESSAGE_ERROR   = 5,
    MESSAGE_VERSION = 6
};

/* Error codes. */
enum error_codes {
    ERROR_INTERNAL        = 1,  /* Internal server failure. */
    ERROR_BAD_TOKEN       = 2,  /* Invalid format in token. */
    ERROR_UNKNOWN_MESSAGE = 3,  /* Unknown message type. */
    ERROR_BAD_COMMAND     = 4,  /* Invalid command format in token. */
    ERROR_UNKNOWN_COMMAND = 5,  /* Unknown command. */
    ERROR_ACCESS          = 6,  /* Access denied. */
    ERROR_TOOMANY_ARGS    = 7,  /* Argument count exceeds server limit. */
    ERROR_TOOMUCH_DATA    = 8   /* Argument size exceeds server limit. */
};

/* Default to a hidden visibility for all util functions. */
#pragma GCC visibility push(hidden)

/*
 * Sending and receiving tokens.  Do not use gss_release_buffer to free the
 * token returned by token_recv; this will cause crashes on Windows.  Call
 * free on the value member instead.
 */
enum token_status token_send(int fd, int flags, gss_buffer_t);
enum token_status token_recv(int fd, int *flags, gss_buffer_t, size_t max);

/*
 * The same, but with a GSS-API protection layer applied.  On a GSS-API
 * failure, the major and minor status are returned in the final two
 * arguments.
 */
enum token_status token_send_priv(int fd, gss_ctx_id_t, int flags,
                                  gss_buffer_t, OM_uint32 *, OM_uint32 *);
enum token_status token_recv_priv(int fd, gss_ctx_id_t, int *flags,
                                  gss_buffer_t, size_t max, OM_uint32 *,
                                  OM_uint32 *);

/*
 * Convert a GSS-API error code pair into a human-readable string.  Returns a
 * newly allocated string that the caller must free.
 */
char *gssapi_error_string(const char *prefix, OM_uint32, OM_uint32);

/* Concatenate NULL-terminated strings into a newly allocated string. */
char *concat(const char *first, ...);

/*
 * Given a base path and a file name, create a newly allocated path string.
 * The name will be appended to base with a / between them.  Exceptionally, if
 * name begins with a slash, it will be strdup'd and returned as-is.
 */
char *concatpath(const char *base, const char *name);

/*
 * Like the non-x versions of the same function, but keep writing until either
 * the write is not making progress or there's a real error.  Handle partial
 * writes and EINTR/EAGAIN errors.
 */
ssize_t xpwrite(int fd, const void *buffer, size_t size, off_t offset);
ssize_t xwrite(int fd, const void *buffer, size_t size);
ssize_t xwritev(int fd, const struct iovec *iov, int iovcnt);

/*
 * Create a socket and bind it to the specified address and port (either IPv4
 * or IPv6), returning the resulting file descriptor or -1 on error.  Errors
 * are reported using warn/syswarn.  To bind to all interfaces, use "any" or
 * "all" for address.
 */
int network_bind_ipv4(const char *address, unsigned short port);
int network_bind_ipv6(const char *address, unsigned short port);

/*
 * Create and bind sockets for every local address (normally two, one for IPv4
 * and one for IPv6, if IPv6 support is enabled).  If IPv6 is not enabled,
 * just one socket will be created and bound to the IPv4 wildcard address.
 * fds will be set to an array containing the resulting file descriptors, with
 * count holding the count returned.
 */
void network_bind_all(unsigned short port, int **fds, int *count);

/*
 * Create a socket and connect it to the remote service given by the linked
 * list of addrinfo structs.  Returns the new file descriptor on success and
 * -1 on failure, with the error left in errno.  Takes an optional source
 * address.
 */
int network_connect(struct addrinfo *, const char *source);

/*
 * Like network_connect but takes a host and port instead.  If host lookup
 * fails, errno may not be set to anything useful.
 */
int network_connect_host(const char *host, unsigned short port,
                         const char *source);

/*
 * Creates a socket of the specified domain and type and binds it to the
 * appropriate source address, either the one supplied or the appropriate
 * innconf setting if the provided source address is NULL.  To bind to all
 * interfaces, use "all" for address.  Returns the newly created file
 * descriptor or -1 on error.
 *
 * This is a lower-level function intended primarily for the use of clients
 * that will then go on to do a non-blocking connect.
 */
int network_client_create(int domain, int type, const char *source);

/*
 * Put an ASCII representation of the address in a sockaddr into the provided
 * buffer, which should hold at least INET6_ADDRSTRLEN characters.
 */
bool network_sockaddr_sprint(char *, size_t, const struct sockaddr *);

/*
 * Returns if the addresses from the two sockaddrs are equal.  The ports are
 * ignored, and only AF_INET or AF_INET6 sockaddrs are supported (all others
 * will return false).
 */
bool network_sockaddr_equal(const struct sockaddr *, const struct sockaddr *);

/* Returns the port number from a sockaddr. */
unsigned short network_sockaddr_port(const struct sockaddr *);

/*
 * Compare two addresses relative to an optional mask.  Returns true if
 * they're equal, false otherwise or on a parse error.
 */
bool network_addr_match(const char *, const char *, const char *mask);

/* Set a file descriptor close-on-exec or nonblocking. */
bool fdflag_close_exec(int fd, bool flag);
bool fdflag_nonblocking(int fd, bool flag);

/*
 * The reporting functions.  The ones prefaced by "sys" add a colon, a space,
 * and the results of strerror(errno) to the output and are intended for
 * reporting failures of system calls.
 */
void debug(const char *, ...)
    __attribute__((__format__(printf, 1, 2)));
void notice(const char *, ...)
    __attribute__((__format__(printf, 1, 2)));
void sysnotice(const char *, ...)
    __attribute__((__format__(printf, 1, 2)));
void warn(const char *, ...)
    __attribute__((__format__(printf, 1, 2)));
void syswarn(const char *, ...)
    __attribute__((__format__(printf, 1, 2)));
void die(const char *, ...)
    __attribute__((__noreturn__, __format__(printf, 1, 2)));
void sysdie(const char *, ...)
    __attribute__((__noreturn__, __format__(printf, 1, 2)));

/*
 * Set the handlers for various message functions.  All of these functions
 * take a count of the number of handlers and then function pointers for each
 * of those handlers.  These functions are not thread-safe; they set global
 * variables.
 */
void message_handlers_debug(int count, ...);
void message_handlers_notice(int count, ...);
void message_handlers_warn(int count, ...);
void message_handlers_die(int count, ...);

/*
 * Some useful handlers, intended to be passed to message_handlers_*.  All
 * handlers take the length of the formatted message, the format, a variadic
 * argument list, and the errno setting if any.
 */
void message_log_stdout(int, const char *, va_list, int);
void message_log_stderr(int, const char *, va_list, int);
void message_log_syslog_debug(int, const char *, va_list, int);
void message_log_syslog_info(int, const char *, va_list, int);
void message_log_syslog_notice(int, const char *, va_list, int);
void message_log_syslog_warning(int, const char *, va_list, int);
void message_log_syslog_err(int, const char *, va_list, int);
void message_log_syslog_crit(int, const char *, va_list, int);

/* The type of a message handler. */
typedef void (*message_handler_func)(int, const char *, va_list, int);

/* If non-NULL, called before exit and its return value passed to exit. */
extern int (*message_fatal_cleanup)(void);

/*
 * If non-NULL, prepended (followed by ": ") to all messages printed by either
 * message_log_stdout or message_log_stderr.
 */
extern const char *message_program_name;

struct vector {
    size_t count;
    size_t allocated;
    char **strings;
};

struct cvector {
    size_t count;
    size_t allocated;
    const char **strings;
};

/* Create a new, empty vector. */
struct vector *vector_new(void);
struct cvector *cvector_new(void);

/* Add a string to a vector.  Resizes the vector if necessary. */
void vector_add(struct vector *, const char *string);
void cvector_add(struct cvector *, const char *string);

/* Add a counted string to a vector.  Only available for vectors. */
void vector_addn(struct vector *, const char *string, size_t length);

/*
 * Resize the array of strings to hold size entries.  Saves reallocation work
 * in vector_add if it's known in advance how many entries there will be.
 */
void vector_resize(struct vector *, size_t size);
void cvector_resize(struct cvector *, size_t size);

/*
 * Reset the number of elements to zero, freeing all of the strings for a
 * regular vector, but not freeing the strings array (to cut down on memory
 * allocations if the vector will be reused).
 */
void vector_clear(struct vector *);
void cvector_clear(struct cvector *);

/* Free the vector and all resources allocated for it. */
void vector_free(struct vector *);
void cvector_free(struct cvector *);

/*
 * Split functions build a vector from a string.  vector_split splits on a
 * specified character, while vector_split_space splits on any sequence of
 * spaces or tabs (not any sequence of whitespace, as just spaces or tabs is
 * more useful).  The cvector versions destructively modify the provided
 * string in-place to insert nul characters between the strings.  If the
 * vector argument is NULL, a new vector is allocated; otherwise, the provided
 * one is reused.
 *
 * Empty strings will yield zero-length vectors.  Adjacent delimiters are
 * treated as a single delimiter by *_split_space, but *not* by *_split, so
 * callers of *_split should be prepared for zero-length strings in the
 * vector.
 */
struct vector *vector_split(const char *string, char sep, struct vector *);
struct vector *vector_split_space(const char *string, struct vector *);
struct cvector *cvector_split(char *string, char sep, struct cvector *);
struct cvector *cvector_split_space(char *string, struct cvector *);

/*
 * Build a string from a vector by joining its components together with the
 * specified string as separator.  Returns a newly allocated string; caller is
 * responsible for freeing.
 */
char *vector_join(const struct vector *, const char *seperator);
char *cvector_join(const struct cvector *, const char *separator);

/*
 * Exec the given program with the vector as its arguments.  Return behavior
 * is the same as execv.  Note the argument order is different than the other
 * vector functions (but the same as execv).
 */
int vector_exec(const char *path, struct vector *);
int cvector_exec(const char *path, struct cvector *);

/*
 * The functions are actually macros so that we can pick up the file and line
 * number information for debugging error messages without the user having to
 * pass those in every time.
 */
#define xcalloc(n, size)        x_calloc((n), (size), __FILE__, __LINE__)
#define xmalloc(size)           x_malloc((size), __FILE__, __LINE__)
#define xrealloc(p, size)       x_realloc((p), (size), __FILE__, __LINE__)
#define xstrdup(p)              x_strdup((p), __FILE__, __LINE__)
#define xstrndup(p, size)       x_strndup((p), (size), __FILE__, __LINE__)
#define xvasprintf(p, f, a)     x_vasprintf((p), (f), (a), __FILE__, __LINE__)

/*
 * asprintf is a special case since it takes variable arguments.  If we have
 * support for variadic macros, we can still pass in the file and line and
 * just need to put them somewhere else in the argument list than last.
 * Otherwise, just call x_asprintf directly.  This means that the number of
 * arguments x_asprintf takes must vary depending on whether variadic macros
 * are supported.
 */
#ifdef HAVE_C99_VAMACROS
# define xasprintf(p, f, ...) \
    x_asprintf((p), __FILE__, __LINE__, (f), __VA_ARGS__)
#elif HAVE_GNU_VAMACROS
# define xasprintf(p, f, args...) \
    x_asprintf((p), __FILE__, __LINE__, (f), args)
#else
# define xasprintf x_asprintf
#endif

/*
 * Last two arguments are always file and line number.  These are internal
 * implementations that should not be called directly.
 */
void *x_calloc(size_t, size_t, const char *, int);
void *x_malloc(size_t, const char *, int);
void *x_realloc(void *, size_t, const char *, int);
char *x_strdup(const char *, const char *, int);
char *x_strndup(const char *, size_t, const char *, int);
int x_vasprintf(char **, const char *, va_list, const char *, int);

/* asprintf special case. */
#if HAVE_C99_VAMACROS || HAVE_GNU_VAMACROS
int x_asprintf(char **, const char *, int, const char *, ...);
#else
int x_asprintf(char **, const char *, ...);
#endif

/* Failure handler takes the function, the size, the file, and the line. */
typedef void (*xmalloc_handler_type)(const char *, size_t, const char *, int);

/* The default error handler. */
void xmalloc_fail(const char *, size_t, const char *, int);

/*
 * Assign to this variable to choose a handler other than the default, which
 * just calls sysdie.
 */
extern xmalloc_handler_type xmalloc_error_handler;

/* Undo default visibility change. */
#pragma GCC visibility pop

END_DECLS

#endif /* UTIL_UTIL_H */
