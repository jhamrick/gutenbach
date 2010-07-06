/*
 * Small C program to verify that standard input is not closed but returns EOF
 * on any read and that all file descriptors higher than 2 are closed.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2007, 2008 Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>

#include <errno.h>

int
main(void)
{
    char buffer;
    ssize_t count;
    int i;

    /* First check that standard input is not closed but returns EOF. */
    count = read(0, &buffer, 1);
    if (count > 0) {
        printf("Read %d bytes\n", (int) count);
        exit(1);
    } else if (count < 0) {
        printf("Failed with error: %s\n", strerror(errno));
        exit(2);
    }

    /*
     * Now, check that all higher file descriptors are closed.  (We only go up
     * to 31; it's very unlikely that there will be problems higher than
     * that.)
     */
    for (i = 3; i < 32; i++)
        if (close(i) >= 0 || errno != EBADF) {
            printf("File descriptor %d was open\n", i);
            exit(3);
        }
    printf("Okay");
    exit(0);
}
