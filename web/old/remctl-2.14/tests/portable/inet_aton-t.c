/*
 * inet_aton test suite.
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

#include <tests/tap/basic.h>

int test_inet_aton(const char *, struct in_addr *);


static void
test_addr(const char *string, unsigned long addr)
{
    int success;
    struct in_addr in;

    success = test_inet_aton(string, &in);
    ok(success, "inet_aton on %s", string);
    is_hex(htonl(addr), in.s_addr, "...matches expected value");
}


static void
test_fail(const char *string)
{
    struct in_addr in;
    int success;

    in.s_addr = htonl(0x01020304UL);
    success = test_inet_aton(string, &in);
    ok(success == 0, "inet_aton on %s fails", string);
    is_hex(htonl(0x01020304UL), in.s_addr, "...and leaves in unchanged");
}


int
main(void)
{
    plan(92);

    test_addr(            "0.0.0.0", 0);
    test_addr(     "127.0.0.000000", 0x7f000000UL);
    test_addr(    "255.255.255.255", 0xffffffffUL);
    test_addr(    "172.200.232.199", 0xacc8e8c7UL);
    test_addr(            "1.2.3.4", 0x01020304UL);

    test_addr(    "0x0.0x0.0x0.0x0", 0);
    test_addr("0x7f.0x000.0x0.0x00", 0x7f000000UL);
    test_addr("0xff.0xFf.0xFF.0xff", 0xffffffffUL);
    test_addr("0xAC.0xc8.0xe8.0xC7", 0xacc8e8c7UL);
    test_addr("0xAa.0xbB.0xCc.0xdD", 0xaabbccddUL);
    test_addr("0xEe.0xfF.0.0x00000", 0xeeff0000UL);
    test_addr("0x1.0x2.0x00003.0x4", 0x01020304UL);

    test_addr(   "000000.00.000.00", 0);
    test_addr(             "0177.0", 0x7f000000UL);
    test_addr("0377.0377.0377.0377", 0xffffffffUL);
    test_addr("0254.0310.0350.0307", 0xacc8e8c7UL);
    test_addr("00001.02.3.00000004", 0x01020304UL);

    test_addr(           "16909060", 0x01020304UL);
    test_addr(      "172.062164307", 0xacc8e8c7UL);
    test_addr(    "172.0xc8.0xe8c7", 0xacc8e8c7UL);
    test_addr(              "127.1", 0x7f000001UL);
    test_addr(         "0xffffffff", 0xffffffffUL);
    test_addr(       "127.0xffffff", 0x7fffffffUL);
    test_addr(     "127.127.0xffff", 0x7f7fffffUL);

    test_fail(                 "");
    test_fail(     "Donald Duck!");
    test_fail(       "a127.0.0.1");
    test_fail(         "aaaabbbb");
    test_fail(      "0x100000000");
    test_fail(      "0xfffffffff");
    test_fail(    "127.0xfffffff");
    test_fail(    "127.376926742");
    test_fail( "127.127.01452466");
    test_fail("127.127.127.0x100");
    test_fail(            "256.0");
    test_fail( "127.0378.127.127");
    test_fail("127.127.0x100.127");
    test_fail(        "127.0.o.1");
    test_fail( "127.127.127.127v");
    test_fail(   "ef.127.127.127");
    test_fail( "0128.127.127.127");
    test_fail(         "0xeg.127");
    test_fail(         ".127.127");
    test_fail(         "127.127.");
    test_fail(         "127..127");
    test_fail(      "de.ad.be.ef");

    return 0;
}
