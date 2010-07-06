dnl gput.m4 -- Find the compiler and linker flags for GPUT.
dnl
dnl Provides the macro RRA_LIB_GPUT, which finds the compiler and linker flags
dnl for linking with GPUT libraries (an authorization system developed at
dnl Carnegie Mellon University) and sets the substitution variables
dnl GPUT_CPPFLAGS, GPUT_LDFLAGS, and GPUT_LIBS.  Provides the --with-gput,
dnl --with-gput-lib, and --with-gput-include configure options and defines
dnl HAVE_GPUT if the library is available.
dnl
dnl Depends on RRA_SET_LDFLAGS.
dnl
dnl Written by Russ Allbery <rra@stanford.edu>
dnl Copyright 2008 Board of Trustees, Leland Stanford Jr. University
dnl
dnl See LICENSE for licensing terms.

AC_DEFUN([RRA_LIB_GPUT],
[GPUT_CPPFLAGS=
 GPUT_LDFLAGS=
 GPUT_LIBS=
 AC_SUBST([GPUT_CPPFLAGS])
 AC_SUBST([GPUT_LDFLAGS])
 AC_SUBST([GPUT_LIBS])
 rra_with_gput=

 AC_ARG_WITH([gput],
    [AC_HELP_STRING([--with-gput=DIR],
        [Location of CMU GPUT headers and libraries])],
    [rra_with_gput=yes
     AS_IF([test x"$withval" = xno],
        [rra_with_gput=no],
        [AS_IF([test x"$withval" != xyes],
            [GPUT_CPPFLAGS="-I$withval/include"
             RRA_SET_LDFLAGS([GPUT_LDFLAGS], [$withval])])])])
 AC_ARG_WITH([gput-include],
    [AC_HELP_STRING([--with-gput-include=DIR],
        [Location of CMU GPUT headers])],
    [AS_IF([test x"$withval" = xyes || test x"$withval" = xno],
        [AC_MSG_ERROR([no argument given for --with-gput-include])])
     rra_with_gput=yes
     GPUT_CPPFLAGS="-I$withval"])
 AC_ARG_WITH([gput-lib],
    [AC_HELP_STRING([--with-gput-lib=DIR], [Location of CMU GPUT libraries])],
    [AS_IF([test x"$withval" = xyes || test x"$withval" = xno],
        [AC_MSG_ERROR([no argument given for --with-gput-lib])])
     rra_with_gput=yes
     GPUT_LDFLAGS="-L$withval"])

 rra_save_CPPFLAGS="$CPPFLAGS"
 rra_save_LDFLAGS="$LDFLAGS"
 CPPFLAGS="$GPUT_CPPFLAGS $CPPFLAGS"
 LDFLAGS="$GPUT_LDFLAGS $LDFLAGS"
 AS_IF([test x"$rra_with_gput" != xno],
    [AC_CHECK_HEADER([gput.h],
        [AC_CHECK_LIB([gput], [gput_open],
            [AC_DEFINE([HAVE_GPUT], 1,
                [Define to 1 if the CMU GPUT library is present])
             GPUT_LIBS=-lgput],
            [AS_IF([test x"$rra_with_gput" = xyes],
                [AC_MSG_ERROR([GPUT library not found])])])],
        [AS_IF([test x"$rra_with_gput" = xyes],
            [AC_MSG_ERROR([GPUT header gput.h not found])])])])])
