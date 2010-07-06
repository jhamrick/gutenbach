/*
 * fdflag test suite.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2008, 2009 Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/socket.h>

#include <errno.h>
#include <sys/wait.h>

#include <tests/tap/basic.h>
#include <util/util.h>


int
main(void)
{
    int master, data, out1, out2;
    socklen_t size;
    ssize_t status;
    struct sockaddr_in sin;
    pid_t child;
    char buffer[] = "D";

    plan(8);

    /* Parent will create the socket first to get the port number. */
    memset(&sin, '\0', sizeof(sin));
    sin.sin_family = AF_INET;
    master = socket(AF_INET, SOCK_STREAM, 0);
    if (master == -1)
        sysbail("socket creation failed");
    if (bind(master, (struct sockaddr *) &sin, sizeof(sin)) < 0)
        sysbail("bind failed");
    size = sizeof(sin);
    if (getsockname(master, (struct sockaddr *) &sin, &size) < 0)
        sysbail("getsockname failed");
    if (listen(master, 1) < 0)
        sysbail("listen failed");

    /* Duplicate standard output to test close-on-exec. */
    out1 = 8;
    out2 = 9;
    if (dup2(fileno(stdout), out1) < 0)
        sysbail("cannot dup stdout to fd 8");
    if (dup2(fileno(stdout), out2) < 0)
        sysbail("cannot dup stdout to fd 9");
    ok(fdflag_close_exec(out1, true), "set fd 8 to close-on-exec");
    ok(fdflag_close_exec(out2, true), "set fd 9 to close-on-exec");
    ok(fdflag_close_exec(out2, false), "set fd 9 back to regular");

    /*
     * Fork, child closes the open socket and then tries to connect, parent
     * calls listen() and accept() on it.  Parent will then set the socket
     * non-blocking and try to read from it to see what happens, then write to
     * the socket and close it, triggering the child close and exit.
     *
     * Before the child exits, it will exec a shell that will print "no" to
     * the duplicate of stdout that the parent created and then the ok to
     * regular stdout.
     */
    child = fork();
    if (child < 0) {
        sysbail("fork failed");
    } else if (child != 0) {
        size = sizeof(sin);
        data = accept(master, (struct sockaddr *) &sin, &size);
        close(master);
        if (data < 0)
            sysbail("accept failed");
        ok(fdflag_nonblocking(data, true), "set socket non-blocking");
        status = read(data, buffer, sizeof(buffer));
        is_int(-1, status, "got -1 from non-blocking read");
        is_int(EAGAIN, errno, "...with EAGAIN errno");
        write(data, buffer, sizeof(buffer));
        close(data);
    } else {
        data = socket(AF_INET, SOCK_STREAM, 0);
        if (data < 0)
            sysbail("child socket failed");
        if (connect(data, (struct sockaddr *) &sin, sizeof(sin)) < 0)
            sysbail("child connect failed");
        read(data, buffer, sizeof(buffer));
        fclose(stderr);
        execlp("sh", "sh", "-c",
               "printf 'not ' >&8; echo ok 7; echo 'ok 8' >&9", (char *) 0);
        sysbail("exec failed");
    }
    waitpid(child, NULL, 0);
    exit(0);
}
