/*
 * vector test suite.
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

#include <sys/wait.h>

#include <tests/tap/basic.h>
#include <util/util.h>


int
main(void)
{
    struct vector *vector;
    struct cvector *cvector;
    const char cstring[] = "This is a\ttest.  ";
    const char tabs[] = "test\t\ting\t";
    static const char nulls1[] = "This\0is\0a\0test.";
    static const char nulls2[] = "This is a\t\0es\0.  ";
    char empty[] = "";
    char buffer[256];
    char *string;
    char *p;
    pid_t child;

    plan(95);

    vector = vector_new();
    ok(vector != NULL, "vector_new returns non-NULL");
    vector_add(vector, cstring);
    is_int(1, vector->count, "vector_add increases count");
    ok(vector->strings[0] != cstring, "...and allocated new memory");
    vector_resize(vector, 4);
    is_int(4, vector->allocated, "vector_resize works");
    vector_add(vector, cstring);
    vector_add(vector, cstring);
    vector_add(vector, cstring);
    is_int(4, vector->allocated, "...and no reallocation when adding strings");
    is_int(4, vector->count, "...and the count matches");
    is_string(cstring, vector->strings[0], "added the right string");
    is_string(cstring, vector->strings[1], "added the right string");
    is_string(cstring, vector->strings[2], "added the right string");
    is_string(cstring, vector->strings[3], "added the right string");
    ok(vector->strings[1] != vector->strings[2], "each pointer is different");
    ok(vector->strings[2] != vector->strings[3], "each pointer is different");
    ok(vector->strings[3] != vector->strings[0], "each pointer is different");
    ok(vector->strings[0] != cstring, "each pointer is different");
    vector_clear(vector);
    is_int(0, vector->count, "vector_clear works");
    is_int(4, vector->allocated, "...but doesn't free the allocation");
    string = xstrdup(cstring);
    vector_add(vector, cstring);
    vector_add(vector, string);
    is_int(2, vector->count, "added two strings to the vector");
    ok(vector->strings[1] != string, "...and the pointers are different");
    vector_resize(vector, 1);
    is_int(1, vector->count, "vector_resize shrinks the vector");
    ok(vector->strings[0] != cstring, "...and the pointer is different");
    vector_addn(vector, cstring, 4);
    is_int(2, vector->count, "vector_addn increments count");
    is_string("This", vector->strings[1], "...and adds the right data");
    vector_free(vector);
    free(string);

    cvector = cvector_new();
    ok(cvector != NULL, "cvector_new returns non-NULL");
    cvector_add(cvector, cstring);
    is_int(1, cvector->count, "cvector_add adds a string");
    ok(cvector->strings[0] == cstring, "...and keeps the same pointer");
    cvector_resize(cvector, 4);
    is_int(4, cvector->allocated, "cvector_resize works");
    cvector_add(cvector, cstring);
    cvector_add(cvector, cstring);
    cvector_add(cvector, cstring);
    is_int(4, cvector->allocated, "...and subsequent adds don't resize");
    is_int(4, cvector->count, "...and the count is right");
    ok(cvector->strings[1] == cvector->strings[2], "all pointers match");
    ok(cvector->strings[2] == cvector->strings[3], "all pointers match");
    ok(cvector->strings[3] == cvector->strings[0], "all pointers match");
    ok(cvector->strings[0] == cstring, "all pointers match");
    cvector_clear(cvector);
    is_int(0, cvector->count, "cvector_clear works");
    is_int(4, cvector->allocated, "...but doesn't free the allocation");
    string = xstrdup(cstring);
    cvector_add(cvector, cstring);
    cvector_add(cvector, string);
    is_int(2, cvector->count, "added two strings to the vector");
    ok(cvector->strings[1] == string, "...and the pointers match");
    cvector_resize(cvector, 1);
    is_int(1, cvector->count, "cvector_resize shrinks the vector");
    ok(cvector->strings[0] == cstring, "...and the pointers match");
    cvector_free(cvector);
    free(string);

    vector = vector_split_space("This is a\ttest.  ", NULL);
    is_int(4, vector->count, "vector_split_space returns right count");
    is_int(4, vector->allocated, "...and allocation");
    is_string("This", vector->strings[0], "...first string");
    is_string("is", vector->strings[1], "...second string");
    is_string("a", vector->strings[2], "...third string");
    is_string("test.", vector->strings[3], "...fourth string");
    vector_add(vector, cstring);
    is_string(cstring, vector->strings[4], "...and can add another");
    ok(vector->strings[4] != cstring, "allocates a new pointer");
    is_int(5, vector->allocated, "allocation goes up by one");
    vector = vector_split(cstring, 't', vector);
    is_int(3, vector->count, "resplitting returns the right count");
    is_int(5, vector->allocated, "...but doesn't change allocation");
    is_string("This is a\t", vector->strings[0], "...first string");
    is_string("es", vector->strings[1], "...second string");
    is_string(".  ", vector->strings[2], "...third string");
    ok(vector->strings[0] != cstring, "...and allocated new string");
    p = vector_join(vector, "fe");
    is_string("This is a\tfeesfe.  ", p, "vector_join works");
    free(p);
    vector_free(vector);

    string = xstrdup(cstring);
    cvector = cvector_split_space(string, NULL);
    is_int(4, cvector->count, "cvector_split_space returns right count");
    is_int(4, cvector->allocated, "...and allocation");
    is_string("This", cvector->strings[0], "...first string");
    is_string("is", cvector->strings[1], "...second string");
    is_string("a", cvector->strings[2], "...third string");
    is_string("test.", cvector->strings[3], "...fourth string");
    ok(memcmp(string, nulls1, 16) == 0, "original string modified in place");
    cvector_add(cvector, cstring);
    ok(cvector->strings[4] == cstring, "cvector_add then works");
    is_int(5, cvector->allocated, "...and allocation increases by one");
    free(string);
    string = xstrdup(cstring);
    cvector = cvector_split(string, 't', cvector);
    is_int(3, cvector->count, "cvector_split into same cvector works");
    is_int(5, cvector->allocated, "...and doesn't lower allocation");
    is_string("This is a\t", cvector->strings[0], "...first string");
    is_string("es", cvector->strings[1], "...second string");
    is_string(".  ", cvector->strings[2], "...third string");
    ok(cvector->strings[0] == string, "no new memory is allocated");
    ok(memcmp(string, nulls2, 18) == 0, "...and string is modified in place");
    p = cvector_join(cvector, "oo");
    is_string("This is a\tooesoo.  ", p, "cvector_join works");
    free(p);
    cvector_free(cvector);
    free(string);

    vector = vector_split("", ' ', NULL);
    is_int(1, vector->count, "vector_split on empty string");
    is_string("", vector->strings[0], "...returns only empty string");
    vector_free(vector);
    cvector = cvector_split(empty, ' ', NULL);
    is_int(1, cvector->count, "cvector_split on empty string");
    is_string("", vector->strings[0], "...returns only empty string");
    cvector_free(cvector);

    vector = vector_split_space("", NULL);
    is_int(0, vector->count, "vector_split_space on empty string");
    vector_free(vector);
    cvector = cvector_split_space(empty, NULL);
    is_int(0, cvector->count, "cvector_split_space on empty string");
    cvector_free(cvector);

    vector = vector_split(tabs, '\t', NULL);
    is_int(4, vector->count, "vector_split on tab string");
    is_string("test", vector->strings[0], "...first string");
    is_string("", vector->strings[1], "...second string");
    is_string("ing", vector->strings[2], "...third string");
    is_string("", vector->strings[3], "...fourth string");
    p = vector_join(vector, "");
    is_string("testing", p, "vector_join with an empty string works");
    free(p);
    vector_free(vector);

    string = xstrdup(tabs);
    cvector = cvector_split(string, '\t', NULL);
    is_int(4, cvector->count, "cvector_split on tab string");
    is_string("test", cvector->strings[0], "...first string");
    is_string("", cvector->strings[1], "...second string");
    is_string("ing", cvector->strings[2], "...third string");
    is_string("", cvector->strings[3], "...fourth string");
    p = cvector_join(cvector, "");
    is_string("testing", p, "cvector_join with an empty string works");
    free(p);
    cvector_free(cvector);
    free(string);

    vector = vector_split_space("foo\nbar", NULL);
    is_int(1, vector->count, "newline is not space for vector_split_space");
    is_string("foo\nbar", vector->strings[0], "...first string");
    vector_free(vector);

    string = xstrdup("foo\nbar");
    cvector = cvector_split_space(string, NULL);
    is_int(1, cvector->count, "newline is not space for cvector_split_space");
    is_string("foo\nbar", cvector->strings[0], "...first string");
    cvector_free(cvector);

    vector = vector_new();
    vector_add(vector, "/bin/sh");
    vector_add(vector, "-c");
    snprintf(buffer, sizeof(buffer), "echo ok %d - vector_exec", testnum++);
    vector_add(vector, buffer);
    child = fork();
    if (child < 0)
        sysbail("unable to fork");
    else if (child == 0)
        if (vector_exec("/bin/sh", vector) < 0)
            sysnotice("# unable to exec /bin/sh");
    waitpid(child, NULL, 0);
    vector_free(vector);

    cvector = cvector_new();
    cvector_add(cvector, "/bin/sh");
    cvector_add(cvector, "-c");
    snprintf(buffer, sizeof(buffer), "echo ok %d - cvector_exec", testnum++);
    cvector_add(cvector, buffer);
    child = fork();
    if (child < 0)
        sysdie("unable to fork");
    else if (child == 0)
        if (cvector_exec("/bin/sh", cvector) < 0)
            syswarn("unable to exec /bin/sh");
    waitpid(child, NULL, 0);
    cvector_free(cvector);

    return 0;
}
