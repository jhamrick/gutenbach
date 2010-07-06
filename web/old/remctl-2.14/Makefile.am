# Makefile.am -- Automake makefile for remctl.
#
# Written by Russ Allbery <rra@stanford.edu>
# Copyright 2006, 2007, 2008, 2009
#     Board of Trustees, Leland Stanford Jr. University
#
# See LICENSE for licensing terms.

# These three lists of files are needed for Perl builds, Python builds, and
# for the test suite and are not generated or touched by configure.  They're
# listed here to be added to EXTRA_DIST and so that they can be copied over
# properly for builddir != srcdir builds.
PERL_FILES = perl/Remctl.xs perl/typemap perl/t/pod.t perl/t/stanford-netdb.t
PHP_FILES = php/README php/php_remctl.c php/test-wrapper php/tests/001.phpt \
	php/tests/002.phpt php/tests/003.phpt
PYTHON_FILES = python/MANIFEST.in python/README python/_remctlmodule.c

AUTOMAKE_OPTIONS = foreign subdir-objects
ACLOCAL_AMFLAGS = -I m4
EXTRA_DIST = LICENSE Makefile.w32 autogen client/libremctl.rc client/mapfile \
	client/remctl.rc config.h.w32 configure.bat docs/api/remctl.pod \
	docs/api/remctl_close.pod docs/api/remctl_command.pod \
	docs/api/remctl_error.pod docs/api/remctl_new.pod \
	docs/api/remctl_open.pod docs/api/remctl_output.pod docs/design.html \
	docs/extending docs/protocol-v3 docs/protocol.txt docs/protocol.html \
	docs/protocol.xml docs/remctl.pod docs/remctld.8.in docs/remctld.pod \
	examples/remctl.conf examples/rsh-wrapper examples/xinetd \
	java/.classpath java/.project java/Makefile java/README \
	java/bcsKeytab.conf java/gss_jaas.conf java/j3.conf java/k5.conf \
	java/org/eyrie/eagle/remctl/Remctl.java \
	java/org/eyrie/eagle/remctl/RemctlClient.java \
	java/org/eyrie/eagle/remctl/RemctlServer.java java/t5.java \
	java/t7.java portable/getaddrinfo.h portable/getnameinfo.h \
	portable/getopt.h portable/gssapi.h portable/macros.h \
	portable/socket.h portable/stdbool.h portable/system.h \
	portable/uio.h portable/winsock.c remctl.spec \
	tests/TESTS tests/client/remctl-t tests/data/README \
	tests/data/acl-bad-include tests/data/acl-bad-syntax \
	tests/data/acl-nonexistant tests/data/acl-recursive \
	tests/data/acl-simple tests/data/acl-too-long tests/data/acl-valid-3 \
	tests/data/acls/VALID_09 tests/data/acls/val\#id \
	tests/data/acls/val.id tests/data/acls/valid tests/data/acls/valid-2 \
	tests/data/acls/val~id tests/data/acls2/valid-4 tests/data/cmd-argv \
	tests/data/cmd-env tests/data/cmd-hello tests/data/cmd-status \
	tests/data/conf-simple tests/data/conf-test \
	tests/data/configs/bad-logmask-1 tests/data/configs/bad-logmask-2 \
	tests/data/configs/bad-logmask-3 tests/data/configs/bad-logmask-4 \
	tests/data/configs/bad-option-1 tests/data/gput \
	tests/docs/pod-spelling-t tests/docs/pod-t tests/tap/kerberos.sh \
	tests/tap/libtap.sh tests/tap/remctl.sh tests/server/misc-t \
	tests/util/xmalloc-t $(PERL_FILES) $(PHP_FILES) $(PYTHON_FILES)

# Set this globally, since we have too many header files that include the
# GSS-API headers even if the code itself doesn't call GSS-API functions.
AM_CPPFLAGS = $(GSSAPI_CPPFLAGS)

lib_LTLIBRARIES = client/libremctl.la
client_libremctl_la_SOURCES = client/api.c client/client-v1.c \
	client/client-v2.c client/error.c client/internal.h client/open.c
client_libremctl_la_LDFLAGS = -version-info 1:2:0 $(VERSION_LDFLAGS) \
	$(GSSAPI_LDFLAGS)
client_libremctl_la_LIBADD = util/libutil.la $(GSSAPI_LIBS)
include_HEADERS = client/remctl.h

noinst_LTLIBRARIES = portable/libportable.la util/libutil.la
portable_libportable_la_SOURCES = portable/dummy.c
portable_libportable_la_LIBADD = $(LTLIBOBJS)
util_libutil_la_SOURCES = util/concat.c util/fdflag.c util/gss-errors.c \
	util/gss-tokens.c util/messages-die.c util/messages.c util/network.c \
	util/tokens.c util/util.h util/vector.c util/xmalloc.c util/xwrite.c
util_libutil_la_LDFLAGS = $(GSSAPI_LDFLAGS)
util_libutil_la_LIBADD = portable/libportable.la $(GSSAPI_LIBS)

bin_PROGRAMS = client/remctl
client_remctl_SOURCES = client/remctl.c
client_remctl_LDADD = client/libremctl.la util/libutil.la

sbin_PROGRAMS = server/remctld
server_remctld_SOURCES = server/commands.c server/config.c server/generic.c \
	server/logging.c server/internal.h server/remctld.c \
	server/server-v1.c server/server-v2.c
server_remctld_CPPFLAGS = -DCONFIG_FILE=\"$(sysconfdir)/remctl.conf\" \
	$(GSSAPI_CPPFLAGS) $(GPUT_CPPFLAGS)
server_remctld_LDFLAGS = $(GSSAPI_LDFLAGS) $(GPUT_LDFLAGS)
server_remctld_LDADD = util/libutil.la $(GSSAPI_LIBS) $(GPUT_LIBS)

dist_man_MANS = docs/api/remctl.3 docs/api/remctl_close.3 \
	docs/api/remctl_command.3 docs/api/remctl_error.3 \
	docs/api/remctl_new.3 docs/api/remctl_open.3 \
	docs/api/remctl_output.3 docs/remctl.1
man_MANS = docs/remctld.8

docs/remctld.8: $(srcdir)/docs/remctld.8.in
	[ -d docs ] || mkdir docs
	sed 's%\(\\f(CI\)*\@sysconfdir\(\\fI\)*\@%$(sysconfdir)%' \
	    < $(srcdir)/docs/remctld.8.in > $@

# Add symlinks for the man pages that document multiple functions.
install-data-hook:
	rm -f $(DESTDIR)$(man3dir)/remctl_result_free.3
	$(LN_S) remctl.3 $(DESTDIR)$(man3dir)/remctl_result_free.3
	rm -f $(DESTDIR)$(man3dir)/remctl_commandv.3
	$(LN_S) remctl_command.3 $(DESTDIR)$(man3dir)/remctl_commandv.3

CLEANFILES = docs/remctld.8 stamp-python
DISTCLEANFILES = perl/Makefile python/MANIFEST
MAINTAINERCLEANFILES = Makefile.in aclocal.m4 build-aux/compile \
	build-aux/config.guess build-aux/config.sub build-aux/depcomp \
	build-aux/install-sh build-aux/ltmain.sh build-aux/missing \
	config.h.in config.h.in~ configure docs/api/*.3 docs/protocol.html \
	docs/protocol.txt docs/remctl.1 docs/remctld.8.in \
	m4/libtool.m4 m4/ltoptions.m4 m4/ltsugar.m4 m4/ltversion.m4 \
	m4/lt~obsolete.m4

# Automake should deal with the first part of this automatically, but it
# doesn't.  Probably a bug in the non-recursive support.  Also run make clean
# in the perl and php directories if needed and clean up after Python.
clean-local:
	-rm -rf server/.libs tests/.libs tests/client/.libs tests/data/.libs \
	    tests/portable/.libs tests/server/.libs tests/util/.libs
	set -e; if [ -f "perl/Makefile" ] ; then \
	    cd perl && $(MAKE) clean ; \
	    cd perl && [ ! -f Makefile.old ] || mv Makefile.old Makefile ; \
	fi
	set -e; if [ -f "php/Makefile" ] ; then \
	    cd php && $(MAKE) clean ; \
	fi
	rm -rf python/build python/dist python/*.pyc

# Remove the test files we copied over if srcdir != builddir.  Also clean the
# Perl, PHP, and Python directories on make distclean if needed.
#
# phpize --clean is stupid and requires that config.m4 exist, but it was
# already deleted by the regular distclean target.  Hack around that.
distclean-local:
	set -e; if [ x"$(builddir)" != x"$(srcdir)" ] ; then \
	    rm -rf php ; \
	    for f in $(PERL_FILES) ; do \
	        rm -f "$(builddir)/$$f" ; \
	    done ; \
	    rmdir perl/t 2>/dev/null || true ; \
	    for f in $(PYTHON_FILES) ; do \
		rm -f "$(builddir)/$$f" ; \
	    done \
	else \
	    if [ -n "$(PHPIZE)" ] ; then \
		cd php && touch config.m4 && $(PHPIZE) --clean ; \
	    fi ; \
	    rm -f php/config.h.in~ php/config.m4 ; \
	fi

# A set of flags for warnings.  Add -O because gcc won't find some warnings
# without optimization turned on, and add -DDEBUG=1 so we'll also compile all
# debugging code and test it.
WARNINGS = -g -O -DDEBUG=1 -Wall -W -Wendif-labels -Wpointer-arith \
	-Wbad-function-cast -Wwrite-strings -Wstrict-prototypes \
	-Wmissing-prototypes -Wnested-externs -Werror

# Suppress some warnings for Perl, PHP, and Python code because the
# auto-generated code doesn't pass them.
PERL_WARNINGS = -Wno-write-strings -Wno-nested-externs -Wno-strict-prototypes
PHP_WARNINGS = -Wno-strict-prototypes -Wno-write-strings \
	-Wno-missing-prototypes -Wno-unused-parameter
PYTHON_WARNINGS = -Wno-unused-parameter

warnings:
	$(MAKE) CFLAGS='$(WARNINGS)'
	$(MAKE) CFLAGS='$(WARNINGS)' $(check_PROGRAMS)

# The bits below are for the test suite, not for the main package.
check_PROGRAMS = tests/runtests tests/client/api-t tests/client/large-t \
	tests/client/open-t tests/data/cmd-background tests/data/cmd-closed \
	tests/data/cmd-stdin tests/data/cmd-streaming \
	tests/portable/asprintf-t tests/portable/daemon-t \
	tests/portable/getaddrinfo-t tests/portable/getnameinfo-t \
	tests/portable/getopt-t tests/portable/inet_aton-t \
	tests/portable/inet_ntoa-t tests/portable/inet_ntop-t \
	tests/portable/setenv-t tests/portable/snprintf-t \
	tests/portable/strlcat-t tests/portable/strlcpy-t \
	tests/server/accept-t tests/server/acl-t tests/server/config-t \
	tests/server/continue-t tests/server/env-t tests/server/errors-t \
	tests/server/invalid-t tests/server/logging-t tests/server/stdin-t \
	tests/server/streaming-t tests/server/version-t tests/util/concat-t \
	tests/util/fdflag-t tests/util/gss-tokens-t tests/util/messages-t \
	tests/util/network-t tests/util/tokens-t tests/util/vector-t \
	tests/util/xmalloc tests/util/xwrite-t
check_LIBRARIES = tests/tap/libtap.a
tests_runtests_CPPFLAGS =  -DSOURCE='"$(abs_top_srcdir)/tests"' \
	-DBUILD='"$(abs_top_builddir)/tests"'
tests_tap_libtap_a_CPPFLAGS = -I$(abs_top_srcdir)/tests
tests_tap_libtap_a_SOURCES = tests/tap/basic.c tests/tap/basic.h \
	tests/tap/kerberos.h tests/tap/kinit.c tests/tap/messages.c \
	tests/tap/messages.h tests/tap/remctl.c tests/tap/remctl.h

# Used for server tests.
SERVER_FILES = server/commands.c server/config.c server/generic.c \
	server/logging.c server/server-v1.c server/server-v2.c

# All of the test programs.
tests_client_api_t_LDADD = client/libremctl.la tests/tap/libtap.a \
	util/libutil.la
tests_client_open_t_LDFLAGS = $(GSSAPI_LDFLAGS)
tests_client_open_t_LDADD = client/libremctl.la tests/tap/libtap.a \
	util/libutil.la $(GSSAPI_LIBS)
tests_client_large_t_LDADD = client/libremctl.la tests/tap/libtap.a \
	util/libutil.la
tests_data_cmd_stdin_LDADD = util/libutil.la
tests_portable_asprintf_t_SOURCES = tests/portable/asprintf-t.c \
	tests/portable/asprintf.c
tests_portable_asprintf_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_portable_daemon_t_SOURCES = tests/portable/daemon-t.c \
	tests/portable/daemon.c
tests_portable_daemon_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_portable_getaddrinfo_t_SOURCES = tests/portable/getaddrinfo-t.c \
	tests/portable/getaddrinfo.c
tests_portable_getaddrinfo_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_portable_getnameinfo_t_SOURCES = tests/portable/getnameinfo-t.c \
	tests/portable/getnameinfo.c
tests_portable_getnameinfo_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_portable_getopt_t_SOURCES = tests/portable/getopt-t.c \
	tests/portable/getopt.c
tests_portable_getopt_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_portable_inet_aton_t_SOURCES = tests/portable/inet_aton-t.c \
	tests/portable/inet_aton.c
tests_portable_inet_aton_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_portable_inet_ntoa_t_SOURCES = tests/portable/inet_ntoa-t.c \
	tests/portable/inet_ntoa.c
tests_portable_inet_ntoa_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_portable_inet_ntop_t_SOURCES = tests/portable/inet_ntop-t.c \
	tests/portable/inet_ntop.c
tests_portable_inet_ntop_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_portable_setenv_t_SOURCES = tests/portable/setenv-t.c \
	tests/portable/setenv.c
tests_portable_setenv_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_portable_snprintf_t_SOURCES = tests/portable/snprintf-t.c \
	tests/portable/snprintf.c
tests_portable_snprintf_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_portable_strlcat_t_SOURCES = tests/portable/strlcat-t.c \
	tests/portable/strlcat.c
tests_portable_strlcat_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_portable_strlcpy_t_SOURCES = tests/portable/strlcpy-t.c \
	tests/portable/strlcpy.c
tests_portable_strlcpy_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_server_accept_t_SOURCES = tests/server/accept-t.c $(SERVER_FILES)
tests_server_accept_t_LDFLAGS = $(GSSAPI_LDFLAGS) $(GPUT_LDFLAGS)
tests_server_accept_t_LDADD = tests/tap/libtap.a util/libutil.la \
	$(GSSAPI_LIBS) $(GPUT_LIBS)
tests_server_acl_t_SOURCES = tests/server/acl-t.c $(SERVER_FILES)
tests_server_acl_t_LDFLAGS = $(GPUT_LDFLAGS)
tests_server_acl_t_LDADD = tests/tap/libtap.a util/libutil.la $(GPUT_LIBS)
tests_server_config_t_SOURCES = tests/server/config-t.c $(SERVER_FILES)
tests_server_config_t_LDFLAGS = $(GPUT_LDFLAGS)
tests_server_config_t_LDADD = tests/tap/libtap.a util/libutil.la $(GPUT_LIBS)
tests_server_continue_t_LDADD = client/libremctl.la tests/tap/libtap.a \
	util/libutil.la
tests_server_env_t_LDADD = client/libremctl.la tests/tap/libtap.a \
	util/libutil.la
tests_server_errors_t_LDADD = client/libremctl.la tests/tap/libtap.a \
	util/libutil.la
tests_server_invalid_t_LDADD = client/libremctl.la tests/tap/libtap.a \
	util/libutil.la
tests_server_logging_t_SOURCES = tests/server/logging-t.c $(SERVER_FILES)
tests_server_logging_t_LDFLAGS = $(GPUT_LDFLAGS)
tests_server_logging_t_LDADD = tests/tap/libtap.a util/libutil.la \
	$(GSSAPI_LIBS) $(GPUT_LIBS)
tests_server_stdin_t_LDADD = client/libremctl.la tests/tap/libtap.a \
	util/libutil.la
tests_server_streaming_t_LDADD = client/libremctl.la tests/tap/libtap.a \
	util/libutil.la
tests_server_version_t_LDFLAGS = $(GSSAPI_LDFLAGS)
tests_server_version_t_LDADD = client/libremctl.la tests/tap/libtap.a \
	util/libutil.la $(GSSAPI_LIBS)
tests_util_concat_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_util_fdflag_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_util_gss_tokens_t_SOURCES = tests/util/faketoken.c \
	tests/util/gss-tokens.c tests/util/gss-tokens-t.c
tests_util_gss_tokens_t_LDFLAGS = $(GSSAPI_LDFLAGS)
tests_util_gss_tokens_t_LDADD = tests/tap/libtap.a util/libutil.la \
	$(GSSAPI_LIBS)
tests_util_messages_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_util_network_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_util_tokens_t_LDFLAGS = $(GSSAPI_LDFLAGS)
tests_util_tokens_t_LDADD = tests/tap/libtap.a util/libutil.la $(GSSAPI_LIBS)
tests_util_vector_t_LDADD = tests/tap/libtap.a util/libutil.la
tests_util_xmalloc_LDADD = util/libutil.la
tests_util_xwrite_t_SOURCES = tests/util/fakewrite.c tests/util/xwrite.c \
	tests/util/xwrite-t.c
tests_util_xwrite_t_LDADD = tests/tap/libtap.a util/libutil.la

check-local: $(check_PROGRAMS)
	cd tests && ./runtests $(abs_top_srcdir)/tests/TESTS
	@set -e; if [ -f perl/Makefile ] ; then \
	    echo '' ; \
	    cd perl && LD_LIBRARY_PATH=$(abs_top_builddir)/client/.libs \
		$(MAKE) test ; \
	fi
	@set -e; if [ -f php/Makefile ] ; then \
	    echo '' ; \
	    cd php && ./test-wrapper "$(abs_top_builddir)" \
		"$(abs_top_srcdir)"; \
	fi
	@set -e; if [ -f python/setup.py ] ; then \
	    echo '' ; \
	    echo 'Testing Python extension' ; \
	    cd python && LD_LIBRARY_PATH=$(abs_top_builddir)/client/.libs \
		PYTHONPATH="`ls -d build/lib.*`" python test_remctl.py ; \
	fi

# Used for hooking in the build of optional language bindings.
BINDINGS =
BINDINGS_INSTALL =

# The following section sets up the Perl module build properly.  Most of the
# complexity is here to handle building outside of the source directory, in
# which case we need to copy various files from the source directory and make
# sure they're up to date since Perl can't handle VPATH builds.

perl/Remctl.o: perl/Remctl.pm $(srcdir)/perl/Remctl.xs $(srcdir)/perl/typemap
	set -e; if [ x"$(builddir)" != x"$(srcdir)" ] ; then \
	    for f in $(PERL_FILES) ; do \
	        cp "$(srcdir)/$$f" "$(builddir)/$$f" ; \
	    done \
	fi
	cd perl && perl Makefile.PL
	cd perl && $(MAKE) OPTIMIZE="$(CFLAGS) $(PERL_WARNINGS)"

install-data-local-perl: perl/Remctl.o
	cd perl && $(MAKE) install DESTDIR=$(DESTDIR)

# Build and install the Perl bindings if desired.
if BUILD_PERL
BINDINGS += perl/Remctl.o
BINDINGS_INSTALL += install-data-local-perl
endif

# The following section sets up the PECL extension for PHP.

php/modules/remctl.so: php/config.m4 php/php_remctl.h \
		$(srcdir)/php/php_remctl.c
	set -e; if [ x"$(builddir)" != x"$(srcdir)" ] ; then \
	    mkdir php/tests 2>/dev/null || true ; \
	    for f in $(PHP_FILES) ; do \
	        cp "$(srcdir)/$$f" "$(builddir)/$$f" ; \
	    done \
	fi
	cd php && $(PHPIZE) --clean && $(PHPIZE)
	cd php && ./configure CPPFLAGS="$(CPPFLAGS)" \
	    CFLAGS="$(CFLAGS) $(PHP_WARNINGS)" LDFLAGS="$(LDFLAGS)"
	cd php && $(MAKE) CFLAGS="$(CFLAGS) $(PHP_WARNINGS)"

# PHP's build system uses INSTALL_ROOT where everyone else uses DESTDIR.
install-data-local-php: php/modules/remctl.so
	cd php && $(MAKE) install INSTALL_ROOT=$(DESTDIR)

# Build and install the PHP bindings if desired.
if BUILD_PHP
BINDINGS += php/modules/remctl.so
BINDINGS_INSTALL += install-data-local-php
endif

# The following section sets up the Python extension build properly.  Most of
# the complexity is here to handle building outside of the source directory,
# in which case we need to copy various files from the source directory and
# make sure they're up to date.

stamp-python: $(srcdir)/python/_remctlmodule.c python/remctl.py
	set -e; if [ x"$(builddir)" != x"$(srcdir)" ] ; then \
	    for f in $(PYTHON_FILES) ; do \
		cp "$(srcdir)/$$f" "$(builddir)/$$f" ; \
	    done \
	fi
	cd python && CFLAGS="$(CFLAGS) $(PYTHON_WARNINGS)" \
	    python setup.py build
	touch stamp-python

install-data-local-python: stamp-python
	if [ -n "$(DESTDIR)" ] ; then \
	    cd python && python setup.py install --root $(DESTDIR) ; \
	else \
	    cd python && python setup.py install ; \
	fi

# Build and install the Python bindings if desired.
if BUILD_PYTHON
BINDINGS += stamp-python
BINDINGS_INSTALL += install-data-local-python
endif


all-local: $(BINDINGS)
install-data-local: $(BINDINGS_INSTALL)
