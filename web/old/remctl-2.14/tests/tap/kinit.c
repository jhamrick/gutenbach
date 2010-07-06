/*
 * Utility functions for tests that use Kerberos.
 *
 * Currently only provides kerberos_setup(), which assumes a particular set of
 * data files in either the SOURCE or BUILD directories and, using those,
 * obtains Kerberos credentials, sets up a ticket cache, and sets the
 * environment variable pointing to the Kerberos keytab to use for testing.
 *
 * Copyright 2006, 2007, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>

#include <krb5.h>

#include <tests/tap/basic.h>
#include <tests/tap/kerberos.h>
#include <util/util.h>


/*
 * Given the partial path to a file, look under BUILD and then SOURCE for the
 * file and return the full path to the file in newly-allocated memory.
 * Returns NULL if the file doesn't exist.
 */
static char *
find_file(const char *file)
{
    char *base;
    char *path = NULL;
    const char *envs[] = { "BUILD", "SOURCE", NULL };
    int i;

    for (i = 0; envs[i] != NULL; i++) {
        base = getenv(envs[i]);
        if (base == NULL)
            continue;
        path = concatpath(base, file);
        if (access(path, R_OK) == 0)
            break;
        free(path);
        path = NULL;
    }
    return path;
}


/*
 * Obtain Kerberos tickets for the principal specified in test.principal using
 * the keytab specified in test.keytab, both of which are presumed to be in
 * tests/data in either the build or the source tree.
 *
 * Returns the contents of test.principal in newly allocated memory or NULL if
 * Kerberos tests are apparently not configured.  If Kerberos tests are
 * configured but something else fails, calls bail().
 */
char *
kerberos_setup(void)
{
    static const char format1[]
        = "kinit -k -t %s %s >/dev/null 2>&1 </dev/null";
    static const char format2[]
        = "kinit -t %s %s >/dev/null 2>&1 </dev/null";
    static const char format3[]
        = "kinit -k -K %s %s >/dev/null 2>&1 </dev/null";
    FILE *file;
    char *path;
    const char *build;
    char principal[BUFSIZ], *command;
    size_t length;
    int status;

    /* Read the principal name and find the keytab file. */
    path = find_file("data/test.principal");
    if (path == NULL)
        return NULL;
    file = fopen(path, "r");
    if (file == NULL) {
        free(path);
        return NULL;
    }
    if (fgets(principal, sizeof(principal), file) == NULL) {
        fclose(file);
        bail("cannot read %s", path);
    }
    fclose(file);
    if (principal[strlen(principal) - 1] != '\n')
        bail("no newline in %s", path);
    free(path);
    principal[strlen(principal) - 1] = '\0';
    path = find_file("data/test.keytab");
    if (path == NULL)
        return NULL;

    /* Set the KRB5CCNAME and KRB5_KTNAME environment variables. */
    build = getenv("BUILD");
    if (build == NULL)
        build = ".";
    putenv(concat("KRB5CCNAME=", build, "/data/test.cache", (char *) 0));
    putenv(concat("KRB5_KTNAME=", path, (char *) 0));

    /* Now do the Kerberos initialization. */
    length = strlen(format1) + strlen(path) + strlen(principal);
    command = xmalloc(length);
    snprintf(command, length, format1, path, principal);
    status = system(command);
    free(command);
    if (status == -1 || WEXITSTATUS(status) != 0) {
        length = strlen(format2) + strlen(path) + strlen(principal);
        command = xmalloc(length);
        snprintf(command, length, format2, path, principal);
        status = system(command);
        free(command);
    }
    if (status == -1 || WEXITSTATUS(status) != 0) {
        length = strlen(format3) + strlen(path) + strlen(principal);
        command = xmalloc(length);
        snprintf(command, length, format3, path, principal);
        status = system(command);
        free(command);
    }
    if (status == -1 || WEXITSTATUS(status) != 0)
        return NULL;
    free(path);
    return xstrdup(principal);
}


/*
 * Clean up at the end of a test.  Currently, all this does is remove the
 * ticket cache.
 */
void
kerberos_cleanup(void)
{
    char *path;

    path = concatpath(getenv("BUILD"), "data/test.cache");
    unlink(path);
    free(path);
}
