/*
 * Test suite for the server ACL checking.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2007, 2008, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 * Copyright 2008 Carnegie Mellon University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>

#include <server/internal.h>
#include <tests/tap/basic.h>
#include <tests/tap/messages.h>
#include <util/util.h>


int
main(void)
{
    struct confline confline = {
        NULL, 0, NULL, NULL, NULL, NULL, NULL, 0, NULL
    };
    const char *acls[5];

    plan(56);
    if (chdir(getenv("SOURCE")) < 0)
        sysbail("can't chdir to SOURCE");

    confline.file = (char *) "TEST";
    confline.acls = (char **) acls;
    acls[0] = "data/acl-simple";
    acls[1] = NULL;
    acls[2] = NULL;
    acls[3] = NULL;
    acls[4] = NULL;

    ok(server_config_acl_permit(&confline, "rra@example.org"), "simple 1");
    ok(server_config_acl_permit(&confline, "rra@EXAMPLE.COM"), "simple 2");
    ok(server_config_acl_permit(&confline, "cindy@EXAMPLE.COM"), "simple 3");
    ok(server_config_acl_permit(&confline, "test@EXAMPLE.COM"), "simple 4");
    ok(server_config_acl_permit(&confline, "test2@EXAMPLE.COM"), "simple 5");

    ok(!server_config_acl_permit(&confline, "rra@EXAMPLE.ORG"), "no 1");
    ok(!server_config_acl_permit(&confline, "rra@example.com"), "no 2");
    ok(!server_config_acl_permit(&confline, "paul@EXAMPLE.COM"), "no 3");
    ok(!server_config_acl_permit(&confline, "peter@EXAMPLE.COM"), "no 4");

    /* Okay, now capture and check the errors. */
    acls[0] = "data/acl-bad-include";
    acls[1] = "data/acls/valid";
    errors_capture();
    ok(!server_config_acl_permit(&confline, "test@EXAMPLE.COM"),
       "included file not found");
    is_string("data/acl-bad-include:1: included file data/acl-nosuchfile"
              " not found\n", errors, "...and correct error message");
    acls[0] = "data/acl-recursive";
    errors_capture();
    ok(!server_config_acl_permit(&confline, "test@EXAMPLE.COM"),
       "recursive ACL inclusion");
    is_string("data/acl-recursive:3: data/acl-recursive recursively"
              " included\n", errors, "...and correct error message");
    acls[0] = "data/acls/valid-2";
    acls[1] = "data/acl-too-long";
    errors_capture();
    ok(server_config_acl_permit(&confline, "test2@EXAMPLE.COM"),
       "granted access based on first ACL file");
    ok(errors == NULL, "...with no errors");
    ok(!server_config_acl_permit(&confline, "test@EXAMPLE.COM"),
       "...but failed when we hit second file with long line");
    is_string("data/acl-too-long:1: ACL file line too long\n", errors,
              "...with correct error message");
    acls[0] = "data/acl-no-such-file";
    acls[1] = "data/acls/valid";
    errors_capture();
    ok(!server_config_acl_permit(&confline, "test@EXAMPLE.COM"),
       "no such ACL file");
    is_string("TEST:0: included file data/acl-no-such-file not found\n",
              errors, "...with correct error message");
    errors_capture();
    ok(!server_config_acl_permit(&confline, "test2@EXAMPLE.COM"),
       "...even with a principal in an ACL file");
    is_string("TEST:0: included file data/acl-no-such-file not found\n",
              errors, "...still with right error message");
    acls[0] = "data/acl-bad-syntax";
    errors_capture();
    ok(!server_config_acl_permit(&confline, "test@EXAMPLE.COM"),
       "incorrect syntax");
    is_string("data/acl-bad-syntax:2: parse error\n", errors,
              "...with correct error message");
    errors_uncapture();

    /* Check that file: works at the top level. */
    acls[0] = "file:data/acl-simple";
    acls[1] = NULL;
    ok(server_config_acl_permit(&confline, "rra@example.org"),
       "file: success");
    ok(!server_config_acl_permit(&confline, "rra@EXAMPLE.ORG"),
       "file: failure");

    /* Check that include syntax works. */
    ok(server_config_acl_permit(&confline, "incfile@EXAMPLE.ORG"),
       "include 1");
    ok(server_config_acl_permit(&confline, "incfdir@EXAMPLE.ORG"),
       "include 2");
    ok(server_config_acl_permit(&confline, "explicit@EXAMPLE.COM"),
       "include 3");
    ok(server_config_acl_permit(&confline, "direct@EXAMPLE.COM"),
       "include 4");
    ok(server_config_acl_permit(&confline, "good@EXAMPLE.ORG"),
       "include 5");
    ok(!server_config_acl_permit(&confline, "evil@EXAMPLE.ORG"),
       "include failure");

    /* Check that princ: works at the top level. */
    acls[0] = "princ:direct@EXAMPLE.NET";
    ok(server_config_acl_permit(&confline, "direct@EXAMPLE.NET"),
       "princ: success");
    ok(!server_config_acl_permit(&confline, "wrong@EXAMPLE.NET"),
       "princ: failure");

    /* Check that deny: works at the top level. */
    acls[0] = "deny:princ:evil@EXAMPLE.NET";
    acls[1] = "princ:good@EXAMPLE.NET";
    acls[2] = "princ:evil@EXAMPLE.NET";
    acls[3] = NULL;
    ok(server_config_acl_permit(&confline, "good@EXAMPLE.NET"),
       "deny: success");
    ok(!server_config_acl_permit(&confline, "evil@EXAMPLE.NET"),
       "deny: failure");

    /* And make sure deny interacts correctly with files. */
    acls[0] = "data/acl-simple";
    acls[1] = "princ:evil@EXAMPLE.NET";
    acls[2] = NULL;
    ok(!server_config_acl_permit(&confline, "evil@EXAMPLE.NET"),
       "deny in file beats later princ");
    acls[0] = "deny:princ:rra@example.org";
    acls[1] = "data/acl-simple";
    ok(!server_config_acl_permit(&confline, "rra@example.org"),
       "deny overrides later file");

    /*
     * Ensure deny never affirmatively grants access, so deny:deny: matches
     * nothing.
     */
    acls[0] = "deny:deny:princ:rra@example.org";
    acls[1] = "data/acl-simple";
    ok(server_config_acl_permit(&confline, "rra@example.org"),
       "deny:deny does nothing");
    ok(server_config_acl_permit(&confline, "rra@EXAMPLE.COM"),
       "deny:deny doesn't break anything");

    /*
     * Denying a file denies anything that would match the file, and nothing
     * that wouldn't, including due to an embedded deny.
     */
    acls[0] = "deny:file:data/acl-simple";
    acls[1] = "princ:explicit@EXAMPLE.COM";
    acls[2] = "princ:evil@EXAMPLE.ORG";
    acls[3] = "princ:evil@EXAMPLE.NET";
    acls[4] = NULL;
    ok(!server_config_acl_permit(&confline, "explicit@EXAMPLE.COM"),
       "deny of a file works");
    ok(server_config_acl_permit(&confline, "evil@EXAMPLE.ORG"),
       "...and doesn't break anything");
    ok(server_config_acl_permit(&confline, "evil@EXAMPLE.NET"),
       "...and deny inside a denied file is ignored");

    /* Check for an invalid ACL scheme. */
    acls[0] = "ihateyou:verymuch";
    acls[1] = "data/acls/valid";
    errors_capture();
    ok(!server_config_acl_permit(&confline, "test@EXAMPLE.COM"),
       "invalid ACL scheme");
    is_string("TEST:0: invalid ACL scheme 'ihateyou'\n", errors,
              "...with correct error");
    errors_uncapture();

    /*
     * Check for GPUT ACLs and also make sure they behave sanely when GPUT
     * support is not compiled.
     */
    server_config_set_gput_file((char *) "data/gput");
    acls[0] = "gput:test";
    acls[1] = NULL;
#ifdef HAVE_GPUT
    ok(server_config_acl_permit(&confline, "priv@EXAMPLE.ORG"), "GPUT 1");
    ok(!server_config_acl_permit(&confline, "nonpriv@EXAMPLE.ORG"), "GPUT 2");
    ok(!server_config_acl_permit(&confline, "priv@EXAMPLE.NET"), "GPUT 3");
    acls[0] = "gput:test[%@EXAMPLE.NET]";
    ok(server_config_acl_permit(&confline, "priv@EXAMPLE.NET"),
       "GPUT with transform 1");
    ok(!server_config_acl_permit(&confline, "nonpriv@EXAMPLE.NET"),
       "GPUT with transform 2");
    ok(!server_config_acl_permit(&confline, "priv@EXAMPLE.ORG"),
       "GPUT with transform 3");
#else
    errors_capture();
    ok(!server_config_acl_permit(&confline, "priv@EXAMPLE.ORG"), "GPUT");
    is_string("TEST:0: ACL scheme 'gput' is not supported\n", errors,
              "...with not supported error");
    errors_uncapture();
    skip_block(4, "GPUT support not configured");
#endif

    /* Test for valid characters in ACL files. */
    acls[0] = "file:data/acls";
    acls[1] = NULL;
    ok(server_config_acl_permit(&confline, "upcase@EXAMPLE.ORG"),
       "valid chars 1");
    ok(server_config_acl_permit(&confline, "test@EXAMPLE.COM"),
       "valid chars 2");
    ok(server_config_acl_permit(&confline, "test2@EXAMPLE.COM"),
       "valid chars 3");
    ok(!server_config_acl_permit(&confline, "hash@EXAMPLE.ORG"),
       "invalid chars 1");
    ok(!server_config_acl_permit(&confline, "period@EXAMPLE.ORG"),
       "invalid chars 2");
    ok(!server_config_acl_permit(&confline, "tilde@EXAMPLE.ORG"),
       "invalid chars 3");

    return 0;
}
