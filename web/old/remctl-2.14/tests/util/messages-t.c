/*
 * Test suite for error handling routines.
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

#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/wait.h>

#include <tests/tap/basic.h>
#include <util/util.h>

#define END (char *) 0

/* Test function type. */
typedef void (*test_function_t)(void);


/*
 * Fork and execute the provided function, connecting stdout and stderr to a
 * pipe.  Captures the output into the provided buffer and returns the exit
 * status as a waitpid status value.
 */
static int
run_test(test_function_t function, char *buf, size_t buflen)
{
    int fds[2];
    pid_t child;
    ssize_t count, status;
    int rval;

    /* Flush stdout before we start to avoid odd forking issues. */
    fflush(stdout);

    /* Set up the pipe and call the function, collecting its output. */
    if (pipe(fds) == -1)
        sysbail("can't create pipe");
    child = fork();
    if (child == (pid_t) -1) {
        sysbail("can't fork");
    } else if (child == 0) {
        /* In child.  Set up our stdout and stderr. */
        close(fds[0]);
        if (dup2(fds[1], 1) == -1)
            _exit(255);
        if (dup2(fds[1], 2) == -1)
            _exit(255);

        /* Now, run the function and exit successfully if it returns. */
        (*function)();
        fflush(stdout);
        _exit(0);
    } else {
        /*
         * In the parent; close the extra file descriptor, read the output if
         * any, and then collect the exit status.
         */
        close(fds[1]);
        count = 0;
        do {
            status = read(fds[0], buf + count, buflen - count - 1);
            if (status > 0)
                count += status;
        } while (status > 0);
        buf[count < 0 ? 0 : count] = '\0';
        if (waitpid(child, &rval, 0) == (pid_t) -1)
            sysbail("waitpid failed");
    }
    return rval;
}


/*
 * Test functions.
 */
static void test1(void) { warn("warning"); }
static void test2(void) { die("fatal"); }
static void test3(void) { errno = EPERM; syswarn("permissions"); }
static void test4(void) { errno = EACCES; sysdie("fatal access"); }
static void test5(void) {
    message_program_name = "test5";
    warn("warning");
}
static void test6(void) {
    message_program_name = "test6";
    die("fatal");
}
static void test7(void) {
    message_program_name = "test7";
    errno = EPERM;
    syswarn("perms %d", 7);
}
static void test8(void) {
    message_program_name = "test8";
    errno = EACCES;
    sysdie("%st%s", "fa", "al");
}

static int return10(void) { return 10; }

static void test9(void) {
    message_fatal_cleanup = return10;
    die("fatal");
}
static void test10(void) {
    message_program_name = 0;
    message_fatal_cleanup = return10;
    errno = EPERM;
    sysdie("fatal perm");
}
static void test11(void) {
    message_program_name = "test11";
    message_fatal_cleanup = return10;
    errno = EPERM;
    fputs("1st ", stdout);
    sysdie("fatal");
}

static void log_msg(int len, const char *format, va_list args, int error) {
    fprintf(stderr, "%d %d ", len, error);
    vfprintf(stderr, format, args);
    fprintf(stderr, "\n");
}

static void test12(void) {
    message_handlers_warn(1, log_msg);
    warn("warning");
}
static void test13(void) {
    message_handlers_die(1, log_msg);
    die("fatal");
}
static void test14(void) {
    message_handlers_warn(2, log_msg, log_msg);
    errno = EPERM;
    syswarn("warning");
}
static void test15(void) {
    message_handlers_die(2, log_msg, log_msg);
    message_fatal_cleanup = return10;
    errno = EPERM;
    sysdie("fatal");
}
static void test16(void) {
    message_handlers_warn(2, message_log_stderr, log_msg);
    message_program_name = "test16";
    errno = EPERM;
    syswarn("warning");
}
static void test17(void) { notice("notice"); }
static void test18(void) {
    message_program_name = "test18";
    notice("notice");
}
static void test19(void) { debug("debug"); }
static void test20(void) {
    message_handlers_notice(1, log_msg);
    notice("foo");
}
static void test21(void) {
    message_handlers_debug(1, message_log_stdout);
    message_program_name = "test23";
    debug("baz");
}
static void test22(void) {
    message_handlers_die(0);
    die("hi mom!");
}
static void test23(void) {
    message_handlers_warn(0);
    warn("this is a test");
}
static void test24(void) {
    notice("first");
    message_handlers_notice(0);
    notice("second");
    message_handlers_notice(1, message_log_stdout);
    notice("third");
}


/*
 * Given the intended exit status and message and the function to run, check a
 * message test.
 */
static void
test_error(int status, const char *output, test_function_t function)
{
    int real_status;
    char buf[256];

    real_status = run_test(function, buf, sizeof(buf));
    ok(WIFEXITED(real_status), "%d exited", testnum);
    is_int(status, WEXITSTATUS(real_status), "...with right status");
    is_string(output, buf, "...and right output");
}


/*
 * Given the intended status, intended message sans the appended strerror
 * output, errno, and the function to run, check the output.
 */
static void
test_strerror(int status, const char *output, int error,
              test_function_t function)
{
    char *full_output;

    full_output = concat(output, ": ", strerror(error), "\n", END);
    test_error(status, full_output, function);
    free(full_output);
}


/*
 * Run the tests.
 */
int
main(void)
{
    char buff[32];

    plan(24 * 3);

    test_error(0, "warning\n", test1);
    test_error(1, "fatal\n", test2);
    test_strerror(0, "permissions", EPERM, test3);
    test_strerror(1, "fatal access", EACCES, test4);
    test_error(0, "test5: warning\n", test5);
    test_error(1, "test6: fatal\n", test6);
    test_strerror(0, "test7: perms 7", EPERM, test7);
    test_strerror(1, "test8: fatal", EACCES, test8);
    test_error(10, "fatal\n", test9);
    test_strerror(10, "fatal perm", EPERM, test10);
    test_strerror(10, "1st test11: fatal", EPERM, test11);
    test_error(0, "7 0 warning\n", test12);
    test_error(1, "5 0 fatal\n", test13);

    sprintf(buff, "%d", EPERM);

    test_error(0, concat("7 ", buff, " warning\n7 ", buff, " warning\n", END),
               test14);
    test_error(10, concat("5 ", buff, " fatal\n5 ", buff, " fatal\n", END),
               test15);
    test_error(0, concat("test16: warning: ", strerror(EPERM), "\n7 ", buff,
                         " warning\n", END),
               test16);

    test_error(0, "notice\n", test17);
    test_error(0, "test18: notice\n", test18);
    test_error(0, "", test19);
    test_error(0, "3 0 foo\n", test20);
    test_error(0, "test23: baz\n", test21);

    /* Make sure that it's possible to turn off a message type entirely. */ 
    test_error(1, "", test22);
    test_error(0, "", test23);
    test_error(0, "first\nthird\n", test24);

    return 0;
}
