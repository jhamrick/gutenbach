/*
 * asprintf and vasprintf test suite.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2006, 2008, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>

#include <tests/tap/basic.h>

int test_asprintf(char **, const char *, ...);
int test_vasprintf(char **, const char *, va_list);

static int
vatest(char **result, const char *format, ...)
{
    va_list args;
    int status;

    va_start(args, format);
    status = test_vasprintf(result, format, args);
    va_end(args);
    return status;
}

int
main(void)
{
    char *result = NULL;

    plan(12);

    is_int(7, test_asprintf(&result, "%s", "testing"), "asprintf length");
    is_string("testing", result, "asprintf result");
    free(result);
    ok(3, "free asprintf");
    is_int(0, test_asprintf(&result, "%s", ""), "asprintf empty length");
    is_string("", result, "asprintf empty string");
    free(result);
    ok(6, "free asprintf of empty string");

    is_int(6, vatest(&result, "%d %s", 2, "test"), "vasprintf length");
    is_string("2 test", result, "vasprintf result");
    free(result);
    ok(9, "free vasprintf");
    is_int(0, vatest(&result, "%s", ""), "vasprintf empty length");
    is_string("", result, "vasprintf empty string");
    free(result);
    ok(12, "free vasprintf of empty string");

    return 0;
}
