/*
 * Test suite for xwrite and xwritev.
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
#include <portable/uio.h>

#include <tests/tap/basic.h>
#include <util/util.h>

/* The data array we'll use to do testing. */
char data[256];

/* These come from fakewrite. */
extern char write_buffer[];
extern size_t write_offset;
extern int write_interrupt;
extern int write_fail;


static void
test_write(int status, int total, const char *name)
{
    is_int(total, status, "%s return status", name);
    ok(memcmp(data, write_buffer, 256) == 0, "%s output", name);
}


int
main(void)
{
    int i;
    struct iovec iov[4];

    plan(38);

    /* Test xwrite. */
    for (i = 0; i < 256; i++)
        data[i] = i;
    test_write(xwrite(0, data, 256), 256, "xwrite");
    write_offset = 0;
    write_interrupt = 1;
    memset(data, 0, 256);
    test_write(xwrite(0, data, 256), 256, "xwrite interrupted");
    write_offset = 0;
    for (i = 0; i < 32; i++)
        data[i] = i * 2;
    test_write(xwrite(0, data, 32), 32, "xwrite first block");
    for (i = 32; i < 65; i++)
        data[i] = i * 2;
    test_write(xwrite(0, data + 32, 33), 33, "xwrite second block");
    write_offset = 0;
    write_interrupt = 0;

    /* Test xwritev. */
    memset(data, 0, 256);
    iov[0].iov_base = data;
    iov[0].iov_len = 256;
    test_write(xwritev(0, iov, 1), 256, "xwritev");
    write_offset = 0;
    for (i = 0; i < 256; i++)
        data[i] = i;
    iov[0].iov_len = 128;
    iov[1].iov_base = &data[128];
    iov[1].iov_len = 16;
    iov[2].iov_base = &data[144];
    iov[2].iov_len = 112;
    test_write(xwritev(0, iov, 3), 256, "xwritev with multiple iovs");
    write_offset = 0;
    write_interrupt = 1;
    memset(data, 0, 256);
    iov[0].iov_len = 32;
    iov[1].iov_base = &data[32];
    iov[1].iov_len = 224;
    test_write(xwritev(0, iov, 2), 256, "xwritev interrupted");
    for (i = 0; i < 32; i++)
        data[i] = i * 2;
    write_offset = 0;
    test_write(xwritev(0, iov, 1), 32, "xwritev first block");
    for (i = 32; i < 65; i++)
        data[i] = i * 2;
    iov[0].iov_base = &data[32];
    iov[0].iov_len = 16;
    iov[1].iov_base = &data[48];
    iov[1].iov_len = 1;
    iov[2].iov_base = &data[49];
    iov[2].iov_len = 8;
    iov[3].iov_base = &data[57];
    iov[3].iov_len = 8;
    test_write(xwritev(0, iov, 4), 33, "xwritev second block");
    write_offset = 0;
    write_interrupt = 0;

    /* Test xpwrite. */
    for (i = 0; i < 256; i++)
        data[i] = i;
    test_write(xpwrite(0, data, 256, 0), 256, "xpwrite");
    write_interrupt = 1;
    memset(data + 1, 0, 255);
    test_write(xpwrite(0, data + 1, 255, 1), 255, "xpwrite interrupted");
    for (i = 0; i < 32; i++)
        data[i + 32] = i * 2;
    test_write(xpwrite(0, data + 32, 32, 32), 32, "xpwrite first block");
    for (i = 32; i < 65; i++)
        data[i + 32] = i * 2;
    test_write(xpwrite(0, data + 64, 33, 64), 33, "xpwrite second block");
    write_interrupt = 0;

    /* Test failures. */
    write_fail = 1;
    test_write(xwrite(0, data + 1, 255), -1, "xwrite fail");
    iov[0].iov_base = data + 1;
    iov[0].iov_len = 255;
    test_write(xwritev(0, iov, 1), -1, "xwritev fail");
    test_write(xpwrite(0, data + 1, 255, 0), -1, "xpwrite fail");

    /* Test zero-length writes. */
    test_write(xwrite(0, "   ", 0), 0, "xwrite zero length");
    test_write(xpwrite(0, "   ", 0, 2), 0, "xpwrite zero length");
    iov[0].iov_base = data + 1;
    iov[0].iov_len = 2;
    test_write(xwritev(0, iov, 0), 0, "xwritev zero length");

    return 0;
}
