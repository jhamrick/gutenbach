dnl Various checks for socket support and macros.
dnl
dnl This is a collection of various Autoconf macros for checking networking
dnl and socket properties.  The macros provided are:
dnl
dnl     RRA_FUNC_GETADDRINFO_ADDRCONFIG
dnl     RRA_MACRO_IN6_ARE_ADDR_EQUAL
dnl     RRA_MACRO_SA_LEN
dnl
dnl They use a separate internal source macro to make the code easier to read.
dnl
dnl Copyright 2008, 2009 Board of Trustees, Leland Stanford Jr. University
dnl Copyright (c) 2004, 2005, 2006, 2007, 2008, 2009
dnl     by Internet Systems Consortium, Inc. ("ISC")
dnl Copyright (c) 1991, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001,
dnl     2002, 2003 by The Internet Software Consortium and Rich Salz
dnl
dnl See LICENSE for licensing terms.

dnl Source used by RRA_FUNC_GETADDRINFO_ADDRCONFIG.
AC_DEFUN([_RRA_FUNC_GETADDRINFO_ADDRCONFIG_SOURCE], [[
#include <netdb.h>
#include <stdio.h>
#include <sys/socket.h>

int
main(void) {
    struct addrinfo hints, *ai;

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_ADDRCONFIG;
    return (getaddrinfo("localhost", NULL, &hints, &ai) != 0);
}
]])

dnl Check whether the AI_ADDRCONFIG flag works properly with getaddrinfo.
dnl If so, set HAVE_GETADDRINFO_ADDRCONFIG.
AC_DEFUN([RRA_FUNC_GETADDRINFO_ADDRCONFIG],
[AC_CACHE_CHECK([for working AI_ADDRCONFIG flag],
    [rra_cv_func_getaddrinfo_addrconfig_works],
    [AC_RUN_IFELSE(AC_LANG_SOURCE([_RRA_FUNC_GETADDRINFO_ADDRCONFIG_SOURCE]),
        [rra_cv_func_getaddrinfo_addrconfig_works=yes],
        [rra_cv_func_getaddrinfo_addrconfig_works=no],
        [rra_cv_func_getaddrinfo_addrconfig_works=no])])
 AS_IF([test x"$rra_cv_func_getaddrinfo_addrconfig_works" = xyes],
    [AC_DEFINE([HAVE_GETADDRINFO_ADDRCONFIG], 1,
        [Define if the AI_ADDRCONFIG flag works with getaddrinfo.])])])

dnl Source used by INN_IN6_EQ_BROKEN.  Test borrowed from a bug report by
dnl tmoestl@gmx.net for glibc.
AC_DEFUN([_RRA_MACRO_IN6_ARE_ADDR_EQUAL_SOURCE], [[
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int
main (void)
{
    struct in6_addr a;
    struct in6_addr b;

    inet_pton(AF_INET6, "fe80::1234:5678:abcd", &a);
    inet_pton(AF_INET6, "fe80::1234:5678:abcd", &b);
    return IN6_ARE_ADDR_EQUAL(&a, &b) ? 0 : 1;
}
]])

dnl Check whether the IN6_ARE_ADDR_EQUAL macro is broken (like glibc 2.1.3) or
dnl missing.
AC_DEFUN([RRA_MACRO_IN6_ARE_ADDR_EQUAL],
[AC_CACHE_CHECK([whether IN6_ARE_ADDR_EQUAL macro is broken],
    [rra_cv_in6_are_addr_equal_broken],
    [AC_RUN_IFELSE([AC_LANG_SOURCE([_RRA_MACRO_IN6_ARE_ADDR_EQUAL_SOURCE])],
        [rra_cv_in6_are_addr_equal_broken=no],
        [rra_cv_in6_are_addr_equal_broken=yes],
        [rra_cv_in6_are_addr_equal_broken=yes])])
 AS_IF([test x"$rra_cv_in6_are_addr_equal_broken" = xyes],
    [AC_DEFINE([HAVE_BROKEN_IN6_ARE_ADDR_EQUAL], 1,
        [Define if your IN6_ARE_ADDR_EQUAL macro is broken.])])])

dnl Source used by RRA_MACRO_SA_LEN.
AC_DEFUN([_RRA_MACRO_SA_LEN_SOURCE], [[
#include <sys/types.h>
#include <sys/socket.h>

int
main(void)
{
    struct sockaddr sa;
    int x = SA_LEN(&sa);
}
]])

dnl Check whether the SA_LEN macro is available.  This should give the length
dnl of a struct sockaddr regardless of type.
AC_DEFUN([RRA_MACRO_SA_LEN],
[AC_CACHE_CHECK([for SA_LEN macro], [rra_cv_sa_len_macro],
    [AC_LINK_IFELSE([AC_LANG_SOURCE([_RRA_MACRO_SA_LEN_SOURCE])],
        [rra_cv_sa_len_macro=yes],
        [rra_cv_sa_len_macro=no])])
 AS_IF([test "$rra_cv_sa_len_macro" = yes],
    [AC_DEFINE([HAVE_SA_LEN], 1,
        [Define if <sys/socket.h> defines the SA_LEN macro])])])
