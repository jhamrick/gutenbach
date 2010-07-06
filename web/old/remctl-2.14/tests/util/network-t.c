/*
 * network test suite.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2009 Board of Trustees, Leland Stanford Jr. University
 * Copyright (c) 2004, 2005, 2006, 2007
 *     by Internet Systems Consortium, Inc. ("ISC")
 * Copyright (c) 1991, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001,
 *     2002, 2003 by The Internet Software Consortium and Rich Salz
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/socket.h>

#include <ctype.h>
#include <errno.h>
#include <sys/wait.h>

#include <tests/tap/basic.h>
#include <util/util.h>

/* Set this globally to 0 if IPv6 is available but doesn't work. */
static int ipv6 = 1;

/*
 * The server portion of the test.  Listens to a socket and accepts a
 * connection, making sure what is printed on that connection matches what the
 * client is supposed to print.
 */
static void
listener(int fd)
{
    int client;
    FILE *out;
    char buffer[512];

    client = accept(fd, NULL, NULL);
    close(fd);
    if (client < 0) {
        sysnotice("# cannot accept connection from socket");
        ok_block(2, 0, "...socket read test");
    }
    ok(1, "...socket accept");
    out = fdopen(client, "r");
    if (fgets(buffer, sizeof(buffer), out) == NULL) {
        sysnotice("# cannot read from socket");
        ok(0, "...socket read");
    }
    is_string("socket test\r\n", buffer, "...socket read");
    fclose(out);
}


/*
 * Connect to the given host on port 11119 and send a constant string to a
 * socket, used to do the client side of the testing.  Takes the source
 * address as well to pass into network_connect_host.
 */
static void
client(const char *host, const char *source)
{
    int fd;
    FILE *out;

    fd = network_connect_host(host, 11119, source);
    if (fd < 0)
        sysdie("connect failed");
    out = fdopen(fd, "w");
    if (out == NULL)
        sysdie("fdopen failed");
    fputs("socket test\r\n", out);
    fclose(out);
    _exit(0);
}


/*
 * Bring up a server on port 11119 on the loopback address and test connecting
 * to it via IPv4.  Takes an optional source address to use for client
 * connections.
 */
static void
test_ipv4(const char *source)
{
    int fd;
    pid_t child;

    fd = network_bind_ipv4("127.0.0.1", 11119);
    if (fd < 0)
        sysbail("cannot create or bind socket");
    if (listen(fd, 1) < 0) {
        sysnotice("# cannot listen to socket");
        ok_block(3, 0, "IPv4 server test");
    } else {
        ok(1, "IPv4 server test");
        child = fork();
        if (child < 0)
            sysbail("cannot fork");
        else if (child == 0)
            client("127.0.0.1", source);
        else {
            listener(fd);
            waitpid(child, NULL, 0);
        }
    }
}


/*
 * Bring up a server on port 11119 on the loopback address and test connecting
 * to it via IPv6.  Takes an optional source address to use for client
 * connections.
 */
#ifdef HAVE_INET6
static void
test_ipv6(const char *source)
{
    int fd;
    pid_t child;

    fd = network_bind_ipv6("::1", 11119);
    if (fd < 0) {
        if (errno == EAFNOSUPPORT || errno == EPROTONOSUPPORT
            || errno == EADDRNOTAVAIL) {
            ipv6 = 0;
            skip_block(3, "IPv6 not supported");
        } else
            sysbail("cannot create socket");
    }
    if (listen(fd, 1) < 0) {
        sysnotice("# cannot listen to socket");
        ok_block(3, 0, "IPv6 server test");
    } else {
        ok(1, "IPv6 server test");
        child = fork();
        if (child < 0)
            sysbail("cannot fork");
        else if (child == 0)
            client("::1", source);
        else {
            listener(fd);
            waitpid(child, NULL, 0);
        }
    }
}
#else /* !HAVE_INET6 */
static void
test_ipv6(const char *source UNUSED)
{
    skip_block(3, "IPv6 not supported");
}
#endif /* !HAVE_INET6 */


/*
 * Bring up a server on port 11119 on all addresses and try connecting to it
 * via all of the available protocols.  Takes an optional source address to
 * use for client connections.
 */
static void
test_all(const char *source_ipv4, const char *source_ipv6)
{
    int *fds, count, fd, i;
    pid_t child;
    struct sockaddr_storage saddr;
    socklen_t size = sizeof(saddr);

    network_bind_all(11119, &fds, &count);
    if (count == 0)
        sysbail("cannot create or bind socket");
    if (count > 2) {
        notice("# got more than two sockets, using just the first two");
        count = 2;
    }
    for (i = 0; i < count; i++) {
        fd = fds[i];
        if (listen(fd, 1) < 0) {
            sysnotice("# cannot listen to socket %d", fd);
            ok_block(3, 0, "all address server test");
        } else {
            ok(1, "all address server test (part %d)", i);
            child = fork();
            if (child < 0)
                sysbail("cannot fork");
            else if (child == 0) {
                if (getsockname(fd, (struct sockaddr *) &saddr, &size) < 0)
                    sysbail("cannot getsockname");
                if (saddr.ss_family == AF_INET)
                    client("127.0.0.1", source_ipv4);
#ifdef HAVE_INET6
                else if (saddr.ss_family == AF_INET6)
                    client("::1", source_ipv6);
#endif
                else
                    skip_block(2, "unknown socket family %d", saddr.ss_family);
                size = sizeof(saddr);
            } else {
                listener(fd);
                waitpid(child, NULL, 0);
            }
        }
    }
    if (count == 1)
        skip_block(3, "only one listening socket");
}


/*
 * Bring up a server on port 11119 on the loopback address and test connecting
 * to it via IPv4 using network_client_create.  Takes an optional source
 * address to use for client connections.
 */
static void
test_create_ipv4(const char *source)
{
    int fd;
    pid_t child;

    fd = network_bind_ipv4("127.0.0.1", 11119);
    if (fd < 0)
        sysbail("cannot create or bind socket");
    if (listen(fd, 1) < 0) {
        sysnotice("# cannot listen to socket");
        ok_block(3, 0, "IPv4 network client");
    } else {
        ok(1, "IPv4 network client");
        child = fork();
        if (child < 0)
            sysbail("cannot fork");
        else if (child == 0) {
            struct sockaddr_in sin;
            FILE *out;

            fd = network_client_create(PF_INET, SOCK_STREAM, source);
            if (fd < 0)
                _exit(1);
            sin.sin_family = AF_INET;
            sin.sin_port = htons(11119);
            sin.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
            if (connect(fd, (struct sockaddr *) &sin, sizeof(sin)) < 0)
                _exit(1);
            out = fdopen(fd, "w");
            if (out == NULL)
                _exit(1);
            fputs("socket test\r\n", out);
            fclose(out);
            _exit(0);
        } else {
            listener(fd);
            waitpid(child, NULL, 0);
        }
    }
}


/*
 * Tests network_addr_compare.  Takes the expected result, the two addresses,
 * and the mask.
 */
static void
ok_addr(int expected, const char *a, const char *b, const char *mask)
{
    if (expected)
        ok(network_addr_match(a, b, mask), "compare %s %s %s", a, b, mask);
    else
        ok(!network_addr_match(a, b, mask), "compare %s %s %s", a, b, mask);
}


int
main(void)
{
    int status;
    struct addrinfo *ai, *ai4;
    struct addrinfo hints;
    char addr[INET6_ADDRSTRLEN];
    static const char *port = "119";

#ifdef HAVE_INET6
    struct addrinfo *ai6;
    char *p;
    static const char *ipv6_addr = "FEDC:BA98:7654:3210:FEDC:BA98:7654:3210";
#endif

    plan(87);

    /*
     * If IPv6 support appears to be available but doesn't work, we have to
     * skip the test_all tests since they'll create a socket that we then
     * can't connect to.  This is the case on Solaris 8 without IPv6
     * configured.
     */
    test_ipv4(NULL);
    test_ipv6(NULL);
    if (ipv6)
        test_all(NULL, NULL);
    else
        skip_block(6, "IPv6 not configured");
    test_create_ipv4(NULL);

    /* This won't make a difference for loopback connections. */
    test_ipv4("127.0.0.1");
    test_ipv6("::1");
    if (ipv6)
        test_all("127.0.0.1", "::1");
    else
        skip_block(6, "IPv6 not configured");
    test_create_ipv4("127.0.0.1");

    /*
     * Now, test network_sockaddr_sprint, network_sockaddr_equal, and
     * network_sockaddr_port.
     */
    memset(&hints, 0, sizeof(hints));
    hints.ai_flags = AI_NUMERICHOST;
    hints.ai_socktype = SOCK_STREAM;
    status = getaddrinfo("127.0.0.1", port, &hints, &ai4);
    if (status != 0)
        bail("getaddrinfo on 127.0.0.1 failed: %s", gai_strerror(status));
    ok(network_sockaddr_sprint(addr, sizeof(addr), ai4->ai_addr),
       "sprint of 127.0.0.1");
    is_string("127.0.0.1", addr, "...with right results");
    is_int(119, network_sockaddr_port(ai4->ai_addr),
           "sockaddr_port");
    ok(network_sockaddr_equal(ai4->ai_addr, ai4->ai_addr), "sockaddr_equal");
    status = getaddrinfo("127.0.0.2", NULL, &hints, &ai);
    if (status != 0)
        bail("getaddrinfo on 127.0.0.2 failed: %s", gai_strerror(status));
    ok(!network_sockaddr_equal(ai->ai_addr, ai4->ai_addr),
       "sockaddr_equal of unequal addresses");
    ok(!network_sockaddr_equal(ai4->ai_addr, ai->ai_addr),
       "...and the other way around");

    /* The same for IPv6. */
#ifdef HAVE_INET6
    status = getaddrinfo(ipv6_addr, port, &hints, &ai6);
    if (status != 0)
        bail("getaddr on %s failed: %s", ipv6_addr, gai_strerror(status));
    ok(network_sockaddr_sprint(addr, sizeof(addr), ai6->ai_addr),
       "sprint of IPv6 address");
    for (p = addr; *p != '\0'; p++)
        if (islower((unsigned char) *p))
            *p = toupper((unsigned char) *p);
    is_string(ipv6_addr, addr, "...with right results");
    is_int(119, network_sockaddr_port(ai6->ai_addr), "sockaddr_port IPv6");
    ok(network_sockaddr_equal(ai6->ai_addr, ai6->ai_addr),
       "sockaddr_equal IPv6");
    ok(!network_sockaddr_equal(ai4->ai_addr, ai6->ai_addr),
       "...and not equal to IPv4");
    ok(!network_sockaddr_equal(ai6->ai_addr, ai4->ai_addr),
       "...other way around");

    /* Test IPv4 mapped addresses. */
    status = getaddrinfo("::ffff:7f00:1", NULL, &hints, &ai6);
    if (status != 0)
        bail("getaddr on ::ffff:7f00:1 failed: %s", gai_strerror(status));
    ok(network_sockaddr_sprint(addr, sizeof(addr), ai6->ai_addr),
       "sprint of IPv4-mapped address");
    is_string("127.0.0.1", addr, "...with right IPv4 result");
    ok(network_sockaddr_equal(ai4->ai_addr, ai6->ai_addr),
       "sockaddr_equal of IPv4-mapped address");
    ok(network_sockaddr_equal(ai6->ai_addr, ai4->ai_addr),
       "...and other way around");
    ok(!network_sockaddr_equal(ai->ai_addr, ai6->ai_addr),
       "...but not some other address");
    ok(!network_sockaddr_equal(ai6->ai_addr, ai->ai_addr),
       "...and the other way around");
    freeaddrinfo(ai6);
#else
    skip_block(12, "IPv6 not supported");
#endif

    /* Check the domains of functions and their error handling. */
    ai4->ai_addr->sa_family = AF_UNIX;
    ok(!network_sockaddr_equal(ai4->ai_addr, ai4->ai_addr),
       "equal not equal with address mismatches");
    is_int(0, network_sockaddr_port(ai4->ai_addr),
           "port meaningless for AF_UNIX");

    /* Tests for network_addr_compare. */
    ok_addr(1, "127.0.0.1", "127.0.0.1",   NULL);
    ok_addr(0, "127.0.0.1", "127.0.0.2",   NULL);
    ok_addr(1, "127.0.0.1", "127.0.0.0",   "31");
    ok_addr(0, "127.0.0.1", "127.0.0.0",   "32");
    ok_addr(0, "127.0.0.1", "127.0.0.0",   "255.255.255.255");
    ok_addr(1, "127.0.0.1", "127.0.0.0",   "255.255.255.254");
    ok_addr(1, "10.10.4.5", "10.10.4.255", "24");
    ok_addr(0, "10.10.4.5", "10.10.4.255", "25");
    ok_addr(1, "10.10.4.5", "10.10.4.255", "255.255.255.0");
    ok_addr(0, "10.10.4.5", "10.10.4.255", "255.255.255.128");
    ok_addr(0, "129.0.0.0", "1.0.0.0",     "1");
    ok_addr(1, "129.0.0.0", "1.0.0.0",     "0");
    ok_addr(1, "129.0.0.0", "1.0.0.0",     "0.0.0.0");

    /* Try some IPv6 addresses. */
#ifdef HAVE_INET6
    ok_addr(1, ipv6_addr,   ipv6_addr,     NULL);
    ok_addr(1, ipv6_addr,   ipv6_addr,     "128");
    ok_addr(1, ipv6_addr,   ipv6_addr,     "60");
    ok_addr(1, "::127",     "0:0::127",    "128");
    ok_addr(1, "::127",     "0:0::128",    "120");
    ok_addr(0, "::127",     "0:0::128",    "128");
    ok_addr(0, "::7fff",    "0:0::8000",   "113");
    ok_addr(1, "::7fff",    "0:0::8000",   "112");
    ok_addr(0, "::3:ffff",  "::2:ffff",    "120");
    ok_addr(0, "::3:ffff",  "::2:ffff",    "119");
    ok_addr(0, "ffff::1",   "7fff::1",     "1");
    ok_addr(1, "ffff::1",   "7fff::1",     "0");
    ok_addr(0, "fffg::1",   "fffg::1",     NULL);
    ok_addr(0, "ffff::1",   "7fff::1",     "-1");
    ok_addr(0, "ffff::1",   "ffff::1",     "-1");
    ok_addr(0, "ffff::1",   "ffff::1",     "129");
#else
    skip_block(16, "IPv6 not supported");
#endif

    /* Test some invalid addresses. */
    ok_addr(0, "fred",      "fred",        NULL);
    ok_addr(0, "",          "",            NULL);
    ok_addr(0, "",          "",            "0");
    ok_addr(0, "127.0.0.1", "127.0.0.1",   "pete");
    ok_addr(0, "127.0.0.1", "127.0.0.1",   "1p");
    ok_addr(0, "127.0.0.1", "127.0.0.1",   "1p");
    ok_addr(0, "127.0.0.1", "127.0.0.1",   "-1");
    ok_addr(0, "127.0.0.1", "127.0.0.1",   "33");

    return 0;
}
