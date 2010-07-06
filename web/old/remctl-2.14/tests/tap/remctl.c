/*
 * Utility functions for tests that use remctl.
 *
 * Provides functions to start and stop a remctl daemon that uses the test
 * Kerberos environment and runs on port 14373 instead of the default 4373.
 *
 * Copyright 2006, 2007, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>

#include <signal.h>
#include <sys/time.h>
#include <sys/wait.h>

#include <tests/tap/basic.h>
#include <tests/tap/remctl.h>
#include <util/util.h>


/*
 * Start remctld.  Takes the path to remctld, the principal to use as the
 * server principal and the path to the configuration file to use.  Writes the
 * PID file to tests/data/remctl.pid in the BUILD directory and returns the
 * PID file.  If anything fails, calls bail().
 */
pid_t
remctld_start(const char *remctld, const char *principal, const char *config)
{
    char *pidfile;
    pid_t child;
    struct timeval tv;
    size_t n;

    pidfile = concatpath(getenv("BUILD"), "data/remctld.pid");
    if (access(pidfile, F_OK) == 0)
        if (unlink(pidfile) != 0)
            sysbail("cannot delete %s", pidfile);
    child = fork();
    if (child < 0)
        sysbail("fork failed");
    else if (child == 0) {
        if (getenv("VALGRIND") != NULL)
            execl(getenv("VALGRIND"), "valgrind", "--log-file=valgrind.%p",
                  "--leak-check=full", remctld, "-m", "-p", "14373", "-s",
                  principal, "-P", pidfile, "-f", config, "-d", "-S", "-F",
                  (char *) 0);
        else
            execl(remctld, "remctld", "-m", "-p", "14373", "-s", principal,
                  "-P", pidfile, "-f", config, "-d", "-S", "-F", (char *) 0);
        _exit(1);
    } else {
        for (n = 0; n < 100 && access(pidfile, F_OK) != 0; n++) {
            tv.tv_sec = (getenv("VALGRIND") != NULL) ? 1 : 0;
            tv.tv_usec = 10000;
            select(0, NULL, NULL, NULL, &tv);
        }
        if (access(pidfile, F_OK) != 0) {
            kill(child, SIGTERM);
            waitpid(child, NULL, 0);
            bail("cannot start remctld");
        }
        free(pidfile);
        return child;
    }
}


/*
 * Stop remctld.  Takes the PID file of the remctld process.
 */
void
remctld_stop(pid_t child)
{
    char *pidfile;
    struct timeval tv;

    tv.tv_sec = 0;
    tv.tv_usec = 10000;
    select(0, NULL, NULL, NULL, &tv);
    if (waitpid(child, NULL, WNOHANG) == 0) {
        kill(child, SIGTERM);
        waitpid(child, NULL, 0);
    }
    pidfile = concatpath(getenv("BUILD"), "data/remctld.pid");
    unlink(pidfile);
    free(pidfile);
}
