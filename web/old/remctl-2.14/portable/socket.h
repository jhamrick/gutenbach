/*
 * Portability wrapper around <sys/socket.h> and friends.
 *
 * This header file is the equivalent of:
 *
 *     #include <arpa/inet.h>
 *     #include <netinet/in.h>
 *     #include <netdb.h>
 *     #include <sys/socket.h>
 *
 * but also cleans up various messes, mostly related to IPv6 support, and
 * provides a set of portability interfaces that work on both UNIX and
 * Windows.  It ensures that inet_aton, inet_ntoa, and inet_ntop are available
 * and properly prototyped.
 *
 * Copyright 2008 Board of Trustees, Leland Stanford Jr. University
 * Copyright (c) 2004, 2005, 2006, 2007
 *     by Internet Systems Consortium, Inc. ("ISC")
 * Copyright (c) 1991, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001,
 *     2002, 2003 by The Internet Software Consortium and Rich Salz
 *
 * See LICENSE for licensing terms.
 */

#ifndef PORTABLE_SOCKET_H
#define PORTABLE_SOCKET_H 1

#include <config.h>
#include <portable/macros.h>

#include <errno.h>
#include <sys/types.h>

/* BSDI needs <netinet/in.h> before <arpa/inet.h>. */
#ifdef _WIN32
# include <winsock2.h>
# include <ws2tcpip.h>
#else
# include <netinet/in.h>
# include <arpa/inet.h>
# include <netdb.h>
# include <sys/socket.h>
#endif

/*
 * Pick up definitions of getaddrinfo and getnameinfo if not otherwise
 * available.
 */
#include <portable/getaddrinfo.h>
#include <portable/getnameinfo.h>

BEGIN_DECLS

/*
 * Provide prototypes for inet_aton and inet_ntoa if not prototyped in the
 * system header files since they're occasionally available without proper
 * prototypes.
 */
#if !HAVE_DECL_INET_ATON
extern int              inet_aton(const char *, struct in_addr *);
#endif
#if !HAVE_DECL_INET_NTOA
extern const char *     inet_ntoa(const struct in_addr);
#endif
#if !HAVE_INET_NTOP
# ifdef _WIN32
extern const char *     inet_ntop(int, const void *, char *, int);
# else
extern const char *     inet_ntop(int, const void *, char *, socklen_t)
    __attribute__((__visibility__("hidden")));
# endif
#endif

/*
 * Used for portability to Windows, which requires different functions be
 * called to close sockets, send data to or read from sockets, and get socket
 * errors than the regular functions and variables.
 *
 * socket_init must be called before socket functions are used and
 * socket_shutdown at the end of the program.  socket_init may return failure,
 * but this interface doesn't have a way to retrieve the exact error.
 *
 * socket_close, socket_read, and socket_write must be used instead of the
 * standard functions.  On Windows, closesocket must be called instead of
 * close for sockets and recv and send must always be used instead of read and
 * write.
 *
 * When reporting errors from socket functions, use socket_errno and
 * socket_strerror instead of errno and strerror.  When setting errno to
 * something for socket errors (to preserve errors through close, for
 * example), use socket_set_errno instead of just assigning to errno.
 */
#ifdef _WIN32
int socket_init(void);
# define socket_shutdown()      WSACleanup()
# define socket_close(fd)       closesocket(fd)
# define socket_read(fd, b, s)  recv((fd), (b), (s), 0)
# define socket_write(fd, b, s) send((fd), (b), (s), 0)
# define socket_errno           WSAGetLastError()
# define socket_set_errno(e)    WSASetLastError(e)
const char *socket_strerror(int);
#else
# define socket_init()          1
# define socket_shutdown()      /* empty */
# define socket_close(fd)       close(fd)
# define socket_read(fd, b, s)  read((fd), (b), (s))
# define socket_write(fd, b, s) write((fd), (b), (s))
# define socket_errno           errno
# define socket_set_errno(e)    errno = (e)
# define socket_strerror(e)     strerror(e)
#endif

/* Some systems don't define INADDR_LOOPBACK. */
#ifndef INADDR_LOOPBACK
# define INADDR_LOOPBACK 0x7f000001UL
#endif

/*
 * Defined by RFC 3493, used to store a generic address.  Note that this
 * doesn't do the alignment mangling that RFC 3493 does; it's not clear if
 * that needs be added.  However, I've not gotten any complaints yet (probably
 * because nearly everyone now has sockaddr_storage).
 */
#if !HAVE_STRUCT_SOCKADDR_STORAGE
# if HAVE_STRUCT_SOCKADDR_SA_LEN
struct sockaddr_storage {
    unsigned char ss_len;
    unsigned char ss_family;
    unsigned char __padding[128 - 2];
};
# else
struct sockaddr_storage {
    unsigned short ss_family;
    unsigned char __padding[128 - 2];
};
# endif
#endif

/*
 * RFC 2553 used underscores, so some old implementations may have that
 * instead of the non-uglified names from RFC 3493.
 */
#if HAVE_STRUCT_SOCKADDR_STORAGE && !HAVE_STRUCT_SOCKADDR_STORAGE_SS_FAMILY
# define ss_family __ss_family
# define ss_len    __ss_len
#endif

/* Fix IN6_ARE_ADDR_EQUAL if required. */
#ifdef HAVE_BROKEN_IN6_ARE_ADDR_EQUAL
# undef IN6_ARE_ADDR_EQUAL
# define IN6_ARE_ADDR_EQUAL(a, b) \
    (memcmp((a), (b), sizeof(struct in6_addr)) == 0)
#endif

/* Define an SA_LEN macro that gives us the length of a sockaddr. */
#if !HAVE_SA_LEN
# if HAVE_STRUCT_SOCKADDR_SA_LEN
#  define SA_LEN(s)     ((s)->sa_len)
# else
/* Hack courtesy of the USAGI project. */
#  if HAVE_INET6
#   define SA_LEN(s) \
    ((((const struct sockaddr *)(s))->sa_family == AF_INET6)            \
        ? sizeof(struct sockaddr_in6)                                   \
        : ((((const struct sockaddr *)(s))->sa_family == AF_INET)       \
            ? sizeof(struct sockaddr_in)                                \
            : sizeof(struct sockaddr)))
#  else
#   define SA_LEN(s) \
    ((((const struct sockaddr *)(s))->sa_family == AF_INET)             \
        ? sizeof(struct sockaddr_in)                                    \
        : sizeof(struct sockaddr))
#  endif
# endif /* HAVE_SOCKADDR_LEN */
#endif /* !HAVE_SA_LEN_MACRO */

/*
 * AI_ADDRCONFIG results in an error from getaddrinfo on BSD/OS and possibly
 * other platforms.  If configure determined it didn't work, pretend it
 * doesn't exist.
 */
#if !defined(HAVE_GETADDRINFO_ADDRCONFIG) && defined(AI_ADDRCONFIG)
# undef AI_ADDRCONFIG
#endif

/*
 * POSIX requires AI_ADDRCONFIG and AI_NUMERICSERV, but some implementations
 * don't have them yet.  We also may have hidden AI_ADDRCONFIG if it doesn't
 * work.  It's only used in a bitwise OR of flags, so defining them to 0 makes
 * them harmlessly go away.
 */
#ifndef AI_ADDRCONFIG
# define AI_ADDRCONFIG 0
#endif
#ifndef AI_NUMERICSERV
# define AI_NUMERICSERV 0
#endif

/*
 * Constants required by the IPv6 API.  The buffer size required to hold any
 * nul-terminated text representation of the given address type.
 */
#ifndef INET_ADDRSTRLEN
# define INET_ADDRSTRLEN 16
#endif
#ifndef INET6_ADDRSTRLEN
# define INET6_ADDRSTRLEN 46
#endif

/*
 * This is one of the defined error codes from inet_ntop, but it may not be
 * available on systems too old to have that function.
 */
#ifndef EAFNOSUPPORT
# define EAFNOSUPPORT EDOM
#endif

END_DECLS

#endif /* !PORTABLE_SOCKET_H */
