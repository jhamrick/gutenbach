/*
 * strlcpy test suite.
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

#include <tests/tap/basic.h>

size_t test_strlcpy(char *, const char *, size_t);


int
main(void)
{
    char buffer[10];

    plan(23);

    is_int(3, test_strlcpy(buffer, "foo", sizeof(buffer)), "simple strlcpy");
    is_string("foo", buffer, "...result is correct");
    is_int(9, test_strlcpy(buffer, "hello wor", sizeof(buffer)),
           "strlcpy exact length of buffer");
    is_string("hello wor", buffer, "...result is correct");
    is_int(10, test_strlcpy(buffer, "world hell", sizeof(buffer)),
           "strlcpy one more than buffer length");
    is_string("world hel", buffer, "...result is correct");
    ok(buffer[9] == '\0', "...buffer is nul-terminated");
    is_int(11, test_strlcpy(buffer, "hello world", sizeof(buffer)),
           "strlcpy more than buffer length");
    is_string("hello wor", buffer, "...result is correct");
    ok(buffer[9] == '\0', "...buffer is nul-terminated");

    /* Make sure that with a size of 0, the destination isn't changed. */
    is_int(3, test_strlcpy(buffer, "foo", 0), "buffer unchanged if size 0");
    is_string("hello wor", buffer, "...contents still the same");

    /* Now play with empty strings. */
    is_int(0, test_strlcpy(buffer, "", 0), "copy empty string with size 0");
    is_string("hello wor", buffer, "...buffer unchanged");
    is_int(0, test_strlcpy(buffer, "", sizeof(buffer)),
           "copy empty string into full buffer");
    is_string("", buffer, "...buffer now empty string");
    is_int(3, test_strlcpy(buffer, "foo", 2),
           "copy string into buffer of size 2");
    is_string("f", buffer, "...got one character");
    ok(buffer[1] == '\0', "...buffer is nul-terminated");
    is_int(0, test_strlcpy(buffer, "", 1),
           "copy empty string into buffer of size 1");
    ok(buffer[0] == '\0', "...buffer is empty string");

    /* Finally, check using strlcpy as strlen. */
    is_int(3, test_strlcpy(NULL, "foo", 0), "use strlcpy as strlen");
    is_int(11, test_strlcpy(NULL, "hello world", 0), "...again");

    return 0;
}
