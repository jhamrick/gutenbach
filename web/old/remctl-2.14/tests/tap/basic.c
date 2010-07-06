/*
 * Some utility routines for writing tests.
 *
 * Herein are a variety of utility routines for writing tests.  All routines
 * of the form ok*() take a test number and some number of appropriate
 * arguments, check to be sure the results match the expected output using the
 * arguments, and print out something appropriate for that test number.  Other
 * utility routines help in constructing more complex tests.
 *
 * Copyright 2009 Russ Allbery <rra@stanford.edu>
 * Copyright 2006, 2007, 2008
 *     Board of Trustees, Leland Stanford Jr. University
 * Copyright (c) 2004, 2005, 2006
 *     by Internet Systems Consortium, Inc. ("ISC")
 * Copyright (c) 1991, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001,
 *     2002, 2003 by The Internet Software Consortium and Rich Salz
 *
 * See LICENSE for licensing terms.
 */

#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <sys/wait.h>

#include <tap/basic.h>


/*
 * The test count.  Always contains the number that will be used for the next
 * test status.
 */
int testnum = 1;


/*
 * Initialize things.  Turns on line buffering on stdout and then prints out
 * the number of tests in the test suite.
 */
void
plan(int count)
{
    if (setvbuf(stdout, NULL, _IOLBF, BUFSIZ) != 0)
        fprintf(stderr, "cannot set stdout to line buffered: %s\n",
                strerror(errno));
    printf("1..%d\n", count);
    testnum = 1;
}


/*
 * Skip the entire test suite and exits.  Should be called instead of plan(),
 * not after it, since it prints out a special plan line.
 */
void
skip_all(const char *format, ...)
{
    printf("1..0 # skip");
    if (format != NULL) {
        va_list args;

        putchar(' ');
        va_start(args, format);
        vprintf(format, args);
        va_end(args);
    }
    putchar('\n');
    exit(0);
}


/*
 * Print the test description.
 */
static void
print_desc(const char *format, va_list args)
{
    printf(" - ");
    vprintf(format, args);
}


/*
 * Takes a boolean success value and assumes the test passes if that value
 * is true and fails if that value is false.
 */
void
ok(int success, const char *format, ...)
{
    printf("%sok %d", success ? "" : "not ", testnum++);
    if (format != NULL) {
        va_list args;

        va_start(args, format);
        print_desc(format, args);
        va_end(args);
    }
    putchar('\n');
}


/*
 * Skip a test.
 */
void
skip(const char *reason, ...)
{
    printf("ok %d # skip", testnum++);
    if (reason != NULL) {
        va_list args;

        va_start(args, reason);
        putchar(' ');
        vprintf(reason, args);
        va_end(args);
    }
    putchar('\n');
}


/*
 * Report the same status on the next count tests.
 */
void
ok_block(int count, int status, const char *format, ...)
{
    int i;

    for (i = 0; i < count; i++) {
        printf("%sok %d", status ? "" : "not ", testnum++);
        if (format != NULL) {
            va_list args;

            va_start(args, format);
            print_desc(format, args);
            va_end(args);
        }
        putchar('\n');
    }
}


/*
 * Skip the next count tests.
 */
void
skip_block(int count, const char *reason, ...)
{
    int i;

    for (i = 0; i < count; i++) {
        printf("ok %d # skip", testnum++);
        if (reason != NULL) {
            va_list args;

            va_start(args, reason);
            putchar(' ');
            vprintf(reason, args);
            va_end(args);
        }
        putchar('\n');
    }
}


/*
 * Takes an expected integer and a seen integer and assumes the test passes
 * if those two numbers match.
 */
void
is_int(int wanted, int seen, const char *format, ...)
{
    if (wanted == seen)
        printf("ok %d", testnum++);
    else {
        printf("# wanted: %d\n#   seen: %d\n", wanted, seen);
        printf("not ok %d", testnum++);
    }
    if (format != NULL) {
        va_list args;

        va_start(args, format);
        print_desc(format, args);
        va_end(args);
    }
    putchar('\n');
}


/*
 * Takes a string and what the string should be, and assumes the test passes
 * if those strings match (using strcmp).
 */
void
is_string(const char *wanted, const char *seen, const char *format, ...)
{
    if (wanted == NULL)
        wanted = "(null)";
    if (seen == NULL)
        seen = "(null)";
    if (strcmp(wanted, seen) == 0)
        printf("ok %d", testnum++);
    else {
        printf("# wanted: %s\n#   seen: %s\n", wanted, seen);
        printf("not ok %d", testnum++);
    }
    if (format != NULL) {
        va_list args;

        va_start(args, format);
        print_desc(format, args);
        va_end(args);
    }
    putchar('\n');
}


/*
 * Takes an expected integer and a seen integer and assumes the test passes if
 * those two numbers match.
 */
void
is_double(double wanted, double seen, const char *format, ...)
{
    if (wanted == seen)
        printf("ok %d", testnum++);
    else {
        printf("# wanted: %g\n#   seen: %g\n", wanted, seen);
        printf("not ok %d", testnum++);
    }
    if (format != NULL) {
        va_list args;

        va_start(args, format);
        print_desc(format, args);
        va_end(args);
    }
    putchar('\n');
}


/*
 * Takes an expected unsigned long and a seen unsigned long and assumes the
 * test passes if the two numbers match.  Otherwise, reports them in hex.
 */
void
is_hex(unsigned long wanted, unsigned long seen, const char *format, ...)
{
    if (wanted == seen)
        printf("ok %d", testnum++);
    else {
        printf("# wanted: %lx\n#   seen: %lx\n", (unsigned long) wanted,
               (unsigned long) seen);
        printf("not ok %d", testnum++);
    }
    if (format != NULL) {
        va_list args;

        va_start(args, format);
        print_desc(format, args);
        va_end(args);
    }
    putchar('\n');
}


/*
 * Bail out with an error.
 */
void
bail(const char *format, ...)
{
    va_list args;

    fflush(stdout);
    printf("Bail out! ");
    va_start(args, format);
    vprintf(format, args);
    va_end(args);
    printf("\n");
    exit(1);
}


/*
 * Bail out with an error, appending strerror(errno).
 */
void
sysbail(const char *format, ...)
{
    va_list args;
    int oerrno = errno;

    fflush(stdout);
    printf("Bail out! ");
    va_start(args, format);
    vprintf(format, args);
    va_end(args);
    printf(": %s\n", strerror(oerrno));
    exit(1);
}
