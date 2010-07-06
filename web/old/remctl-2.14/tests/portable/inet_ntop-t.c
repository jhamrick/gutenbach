/*
 * inet_ntop test suite.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2009 Board of Trustees, Leland Stanford Jr. University
 * Copyright (c) 2004, 2005, 2006
 *     by Internet Systems Consortium, Inc. ("ISC")
 * Copyright (c) 1991, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001,
 *     2002, 2003 by The Internet Software Consortium and Rich Salz
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/socket.h>

#include <errno.h>

#include <tests/tap/basic.h>

/* Some systems too old to have inet_ntop don't have EAFNOSUPPORT. */
#ifndef EAFNOSUPPORT
# define EAFNOSUPPORT EDOM
#endif

const char *test_inet_ntop(int, const void *, char *, socklen_t);


static void
test_addr(const char *expected, unsigned long addr)
{
    struct in_addr in;
    char result[INET_ADDRSTRLEN];

    in.s_addr = htonl(addr);
    if (test_inet_ntop(AF_INET, &in, result, sizeof(result)) == NULL) {
        printf("# cannot convert %lu: %s", addr, strerror(errno));
        ok(0, "converting %s", expected);
    } else
        ok(1, "converting %s", expected);
    is_string(expected, result, "...with correct result");
}


int
main(void)
{
    plan(6 + 5 * 2);

    ok(test_inet_ntop(AF_UNIX, NULL, NULL, 0) == NULL, "AF_UNIX failure");
    is_int(EAFNOSUPPORT, errno, "...with right errno");
    ok(test_inet_ntop(AF_INET, NULL, NULL, 0) == NULL, "empty buffer");
    is_int(ENOSPC, errno, "...with right errno");
    ok(test_inet_ntop(AF_INET, NULL, NULL, 11) == NULL, "NULL buffer");
    is_int(ENOSPC, errno, "...with right errno");

    test_addr(        "0.0.0.0", 0x0);
    test_addr(      "127.0.0.0", 0x7f000000UL);
    test_addr("255.255.255.255", 0xffffffffUL);
    test_addr("172.200.232.199", 0xacc8e8c7UL);
    test_addr(        "1.2.3.4", 0x01020304UL);

    return 0;
}
