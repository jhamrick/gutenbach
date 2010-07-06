/*
 * Test suite for xmalloc and family.
 *
 * Copyright 2008 Board of Trustees, Leland Stanford Jr. University
 * Copyright 2004, 2005, 2006
 *     by Internet Systems Consortium, Inc. ("ISC")
 * Copyright 1991, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002,
 *     2003 by The Internet Software Consortium and Rich Salz
 *
 * See LICENSE for licensing terms.
 */

#line 1 "xmalloc.c"

#include <config.h>
#include <portable/system.h>

#include <ctype.h>
#include <errno.h>
#include <sys/time.h>

/* Linux requires sys/time.h be included before sys/resource.h. */
#include <sys/resource.h>

#include <util/util.h>


/*
 * A customized error handler for checking xmalloc's support of them.  Prints
 * out the error message and exits with status 1.
 */
static void
test_handler(const char *function, size_t size, const char *file, int line)
{
    die("%s %lu %s %d", function, (unsigned long) size, file, line);
}


/*
 * Allocate the amount of memory given and write to all of it to make sure we
 * can, returning true if that succeeded and false on any sort of detectable
 * error.
 */
static int
test_malloc(size_t size)
{
    char *buffer;
    size_t i;

    buffer = xmalloc(size);
    if (buffer == NULL)
        return 0;
    if (size > 0)
        memset(buffer, 1, size);
    for (i = 0; i < size; i++)
        if (buffer[i] != 1)
            return 0;
    free(buffer);
    return 1;
}


/*
 * Allocate half the memory given, write to it, then reallocate to the desired
 * size, writing to the rest and then checking it all.  Returns true on
 * success, false on any failure.
 */
static int
test_realloc(size_t size)
{
    char *buffer;
    size_t i;

    buffer = xmalloc(10);
    if (buffer == NULL)
        return 0;
    memset(buffer, 1, 10);
    buffer = xrealloc(buffer, size);
    if (buffer == NULL)
        return 0;
    if (size > 0)
        memset(buffer + 10, 2, size - 10);
    for (i = 0; i < 10; i++)
        if (buffer[i] != 1)
            return 0;
    for (i = 10; i < size; i++)
        if (buffer[i] != 2)
            return 0;
    free(buffer);
    return 1;
}


/*
 * Generate a string of the size indicated, call xstrdup on it, and then
 * ensure the result matches.  Returns true on success, false on any failure.
 */
static int
test_strdup(size_t size)
{
    char *string, *copy;
    int match;

    string = xmalloc(size);
    if (string == NULL)
        return 0;
    memset(string, 1, size - 1);
    string[size - 1] = '\0';
    copy = xstrdup(string);
    if (copy == NULL)
        return 0;
    match = strcmp(string, copy);
    free(string);
    free(copy);
    return (match == 0);
}


/*
 * Generate a string of the size indicated plus some, call xstrndup on it, and
 * then ensure the result matches.  Returns true on success, false on any
 * failure.
 */
static int
test_strndup(size_t size)
{
    char *string, *copy;
    int match, toomuch;

    string = xmalloc(size + 1);
    if (string == NULL)
        return 0;
    memset(string, 1, size - 1);
    string[size - 1] = 2;
    string[size] = '\0';
    copy = xstrndup(string, size - 1);
    if (copy == NULL)
        return 0;
    match = strncmp(string, copy, size - 1);
    toomuch = strcmp(string, copy);
    free(string);
    free(copy);
    return (match == 0 && toomuch != 0);
}


/*
 * Allocate the amount of memory given and check that it's all zeroed,
 * returning true if that succeeded and false on any sort of detectable error.
 */
static int
test_calloc(size_t size)
{
    char *buffer;
    size_t i, nelems;

    nelems = size / 4;
    if (nelems * 4 != size)
        return 0;
    buffer = xcalloc(nelems, 4);
    if (buffer == NULL)
        return 0;
    for (i = 0; i < size; i++)
        if (buffer[i] != 0)
            return 0;
    free(buffer);
    return 1;
}


/*
 * Test asprintf with a large string (essentially using it as strdup).
 * Returns true if successful, false otherwise.
 */
static int
test_asprintf(size_t size)
{
    char *copy, *string;
    int status;
    size_t i;

    string = xmalloc(size);
    memset(string, 42, size - 1);
    string[size - 1] = '\0';
    status = xasprintf(&copy, "%s", string);
    free(string);
    for (i = 0; i < size - 1; i++)
        if (copy[i] != 42)
            return 0;
    if (copy[size - 1] != '\0')
        return 0;
    free(copy);
    return 1;
}


/* Wrapper around vasprintf to do the va_list stuff. */
static int
xvasprintf_wrapper(char **strp, const char *format, ...)
{
    va_list args;
    int status;

    va_start(args, format);
    status = xvasprintf(strp, format, args);
    va_end(args);
    return status;
}


/*
 * Test vasprintf with a large string (essentially using it as strdup).
 * Returns true if successful, false otherwise.
 */
static int
test_vasprintf(size_t size)
{
    char *copy, *string;
    int status;
    size_t i;

    string = xmalloc(size);
    memset(string, 42, size - 1);
    string[size - 1] = '\0';
    status = xvasprintf_wrapper(&copy, "%s", string);
    free(string);
    for (i = 0; i < size - 1; i++)
        if (copy[i] != 42)
            return 0;
    if (copy[size - 1] != '\0')
        return 0;
    free(copy);
    return 1;
}


/*
 * Take the amount of memory to allocate in bytes as a command-line argument
 * and call test_malloc with that amount of memory.
 */
int
main(int argc, char *argv[])
{
    size_t size, max;
    size_t limit = 0;
    int willfail = 0;
    unsigned char code;
    struct rlimit rl;
    void *tmp;

    if (argc < 3)
        die("Usage error.  Type, size, and limit must be given.");
    errno = 0;
    size = strtol(argv[2], 0, 10);
    if (size == 0 && errno != 0)
        sysdie("Invalid size");
    errno = 0;
    limit = strtol(argv[3], 0, 10);
    if (limit == 0 && errno != 0)
        sysdie("Invalid limit");

    /* If the code is capitalized, install our customized error handler. */
    code = argv[1][0];
    if (isupper(code)) {
        xmalloc_error_handler = test_handler;
        code = tolower(code);
    }

    /*
     * Decide if the allocation should fail.  If it should, set willfail to 2,
     * so that if it unexpectedly succeeds, we exit with a status indicating
     * that the test should be skipped.
     */
    max = size;
    if (code == 's' || code == 'n' || code == 'a' || code == 'v') {
        max += size;
        if (limit > 0)
            limit += size;
    }
    if (limit > 0 && max > limit)
        willfail = 2;

    /*
     * If a memory limit was given and we can set memory limits, set it.
     * Otherwise, exit 2, signalling to the driver that the test should be
     * skipped.  We do this here rather than in the driver due to some
     * pathological problems with Linux (setting ulimit in the shell caused
     * the shell to die).
     */
    if (limit > 0) {
#if HAVE_SETRLIMIT && defined(RLIMIT_AS)
        rl.rlim_cur = limit;
        rl.rlim_max = limit;
        if (setrlimit(RLIMIT_AS, &rl) < 0) {
            syswarn("Can't set data limit to %lu", (unsigned long) limit);
            exit(2);
        }
        if (size < limit || code == 'r') {
            tmp = malloc(code == 'r' ? 10 : size);
            if (tmp == NULL) {
                syswarn("Can't allocate initial memory of %lu",
                        (unsigned long) size);
                exit(2);
            }
            free(tmp);
        }
#else
        warn("Data limits aren't supported.");
        exit(2);
#endif
    }

    switch (code) {
    case 'c': exit(test_calloc(size) ? willfail : 1);
    case 'm': exit(test_malloc(size) ? willfail : 1);
    case 'r': exit(test_realloc(size) ? willfail : 1);
    case 's': exit(test_strdup(size) ? willfail : 1);
    case 'n': exit(test_strndup(size) ? willfail : 1);
    case 'a': exit(test_asprintf(size) ? willfail : 1);
    case 'v': exit(test_vasprintf(size) ? willfail : 1);
    default:
        die("Unknown mode %c", argv[1][0]);
        break;
    }
    exit(1);
}
