dnl Process this file with autoconf to produce a configure script.
dnl
dnl Written by Russ Allbery <rra@stanford.edu>
dnl Copyright 2002, 2003, 2004, 2005, 2006, 2007, 2008
dnl     Board of Trustees, Leland Stanford Jr. University
dnl
dnl See LICENSE for licensing terms.

AC_PREREQ([2.63])
AC_INIT([remctl], [2.14], [rra@stanford.edu])
AC_CONFIG_AUX_DIR([build-aux])
AC_CONFIG_LIBOBJ_DIR([portable])
AC_CONFIG_MACRO_DIR([m4])
AM_INIT_AUTOMAKE([1.10])
AM_MAINTAINER_MODE

AC_PROG_CC
AC_USE_SYSTEM_EXTENSIONS
AM_PROG_CC_C_O
AC_PROG_INSTALL
AC_PROG_LIBTOOL

AC_SEARCH_LIBS([gethostbyname], [nsl])
AC_SEARCH_LIBS([socket], [socket], ,
    [AC_CHECK_LIB([nsl], [socket], [LIBS="-lnsl -lsocket $LIBS"], ,
        [-lsocket])])
RRA_LIB_GSSAPI
AC_HEADER_STDBOOL
AC_CHECK_HEADERS([sys/bitypes.h sys/filio.h sys/select.h sys/uio.h syslog.h])
AC_CHECK_DECLS([snprintf, vsnprintf])
AC_CHECK_DECLS([inet_aton, inet_ntoa], , ,
    [#include <sys/types.h>
     #include <netinet/in.h>
     #include <arpa/inet.h>])
RRA_C_C99_VAMACROS
RRA_C_GNU_VAMACROS
AC_CHECK_MEMBERS([struct sockaddr.sa_len], , ,
    [#include <sys/types.h>
     #include <sys/socket.h>])
AC_CHECK_TYPES([long long])
AC_CHECK_TYPE([sig_atomic_t], ,
    [AC_DEFINE([sig_atomic_t], [int],
        [Define to int if <signal.h> does not define.])],
    [#include <sys/types.h>
     #include <signal.h>])
AC_CHECK_TYPE([socklen_t], ,
    [AC_DEFINE([socklen_t], [int],
        [Define to int if <sys/socket.h> does not define.])],
    [#include <sys/types.h>
     #include <sys/socket.h>])
AC_CHECK_TYPES([struct sockaddr_in6],
    [AC_DEFINE([HAVE_INET6], [1],
        [Define to 1 if IPv6 library interfaces are available.])], ,
    [#include <sys/types.h>
     #include <netinet/in.h>])
AC_CHECK_TYPES([struct sockaddr_storage],
    [AC_CHECK_MEMBERS([struct sockaddr_storage.ss_family], , ,
        [#include <sys/types.h>
         #include <sys/socket.h>])], ,
    [#include <sys/types.h>
     #include <sys/socket.h>])
RRA_MACRO_IN6_ARE_ADDR_EQUAL
RRA_MACRO_SA_LEN
RRA_FUNC_INET_NTOA
RRA_FUNC_SNPRINTF
AC_CHECK_FUNCS([getaddrinfo],
    [RRA_FUNC_GETADDRINFO_ADDRCONFIG],
    [AC_LIBOBJ([getaddrinfo])])
AC_CHECK_FUNCS([setrlimit setsid])
AC_REPLACE_FUNCS([asprintf daemon getnameinfo getopt inet_aton inet_ntop \
                  setenv strlcat strlcpy])
AC_TYPE_SIGNAL

dnl Additional GSS-API portability checks.
RRA_LIB_GSSAPI_SWITCH
AC_CHECK_HEADERS([gssapi.h])
AC_CHECK_DECL([GSS_C_NT_USER_NAME],
    [AC_DEFINE([HAVE_GSS_RFC_OIDS], 1,
       [Define to 1 if the GSS-API library uses RFC-compliant OIDs.])], ,
[[
#if defined(HAVE_GSSAPI_H)
# include <gssapi.h>
#else
# include <gssapi/gssapi.h>
#endif
]])
AC_CHECK_DECLS([GSS_KRB5_MECHANISM], ,
    [AC_CHECK_DECLS([gss_mech_krb5], ,
        [AC_LIBOBJ([gssapi-mech])],
        [#include <gssapi/gssapi_krb5.h>])],
[[
#if defined(HAVE_GSSAPI_H)
# include <gssapi.h>
#else
# include <gssapi/gssapi.h>
#endif
]])
RRA_LIB_GSSAPI_RESTORE

dnl If and only if we're on a GNU system, use mapfile to do symbol versioning
dnl of the libremctl library.  libtool doesn't know how to do this itself.
dnl This is supported on Solaris as well but we need to know if we're
dnl the GNU linker or the Solaris linker.
case "$host" in
*-gnu*)
    VERSION_LDFLAGS='-Wl,--version-script=${srcdir}/client/mapfile'
    ;;
*)
    VERSION_LDFLAGS=""
    ;;
esac
AC_SUBST([VERSION_LDFLAGS])

dnl Check for the CMU GPUT library.
RRA_LIB_GPUT

dnl Whether to build the Perl bindings.  Put this late so that it shows up
dnl near the bottom of the --help output.
build_perl=
AC_ARG_ENABLE([perl],
    [AC_HELP_STRING([--enable-perl], [Build Perl libremctl bindings])],
    [AS_IF([test x"$enableval" = xyes], [build_perl=yes])])
AM_CONDITIONAL([BUILD_PERL], [test x"$build_perl" = xyes])

dnl Whether to build the PHP bindings.  The dance required to be able to run
dnl phpize before AC_OUTPUT sucks like a sucking thing.
build_php=
AC_ARG_ENABLE([php],
    [AC_HELP_STRING([--enable-php], [Build remctl PECL extension for PHP])],
    [AS_IF([test x"$enableval" = xyes],
        [build_php=yes
         AC_ARG_VAR([PHPIZE], [Path to phpize])
         AC_PATH_PROG([PHPIZE], [phpize])])])
AM_CONDITIONAL([BUILD_PHP], [test x"$build_php" = xyes])

dnl Whether to build the Python bindings.
build_python=
AC_ARG_ENABLE([python],
    [AC_HELP_STRING([--enable-python], [Build Python libremctl bindings])],
    [AS_IF([test x"$enableval" = xyes], [build_python=yes])])
AM_CONDITIONAL([BUILD_PYTHON], [test x"$build_python" = xyes])

AC_CONFIG_FILES([Makefile java/build.xml java/local.properties])
AS_IF([test x"$build_perl" = xyes],
    [AC_CONFIG_FILES([perl/Makefile.PL perl/Remctl.pm])
     AC_CONFIG_FILES([perl/t/api.t], [chmod +x perl/t/api.t])])
AS_IF([test x"$build_php" = xyes],
    [AC_CONFIG_FILES([php/config.m4 php/php_remctl.h])])
AS_IF([test x"$build_python" = xyes],
    [AC_CONFIG_FILES([python/remctl.py python/setup.py])
     AC_CONFIG_FILES([python/test_remctl.py])])
AC_CONFIG_HEADER([config.h])
AC_CONFIG_COMMANDS([docs], [test -d docs || mkdir docs])
AC_OUTPUT
