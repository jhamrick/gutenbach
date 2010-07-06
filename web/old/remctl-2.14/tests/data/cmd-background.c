/*
 * Small C program that outputs a string, forks off a process that sleeps for
 * ten seconds and outputs another string, and meanwhile immediately exits.
 * Used to test that remctld stops listening as soon as its child has exited
 * and doesn't wait forever for output to be closed.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2007 Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>

int
main(void)
{
    pid_t pid;
    FILE *pidfile;

    printf("Parent\n");
    fflush(stdout);
    pid = fork();
    if (pid < 0) {
        fprintf(stderr, "Cannot fork child\n");
        exit(1);
    } else if (pid == 0) {
        pidfile = fopen("data/cmd-background.pid", "w");
        if (pidfile != NULL) {
            fprintf(pidfile, "%lu\n", (unsigned long) getpid());
            fclose(pidfile);
        }
        sleep(10);
        printf("Child\n");
        exit(0);
    }
    return 0;
}
