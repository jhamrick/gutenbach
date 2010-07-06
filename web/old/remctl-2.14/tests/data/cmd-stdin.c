/*
 * Small C program to test handing arguments to programs on standard input.
 * This program supports multiple test modes, selected with the sole
 * command-line argument:
 *
 * read         Read the data first and then output the data read.
 * write        Write "Okay" first and then read the data, then exit.
 * exit         Write "Okay" and exit without reading any data.
 * close        Close stdin, then write "Okay" and exit.
 * nuls         Expects "Test" with a nul after each character.
 * large        Ensure that we read 1MB of As from stdin, then write "Okay".
 * delay        Same as large but with delays in reading.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2009 Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>

#include <errno.h>
#ifdef HAVE_SYS_SELECT_H
# include <sys/select.h>
#endif
#include <sys/time.h>

#include <util/util.h>

int
main(int argc, char *argv[])
{
    char *buffer, *p;
    ssize_t status;
    size_t left, i;
    struct timeval tv;

    if (argc != 3)
        die("expected two arguments, got %d (%s)", argc, argv[2]);
    buffer = xmalloc(1024 * 1024);
    if (strcmp(argv[2], "read") == 0) {
        status = read(0, buffer, 1024 * 1024);
        if (status <= 0)
            sysdie("read failed");
        left = status;
        status = read(0, buffer + status, 1024 * 1024 - status);
        if (status != 0)
            die("didn't get EOF");
        write(1, buffer, left);
    } else if (strcmp(argv[2], "write") == 0) {
        write(1, "Okay", strlen("Okay"));
        status = read(0, buffer, 1024 * 1024);
        if (status <= 0)
            sysdie("read failed");
        status = read(0, buffer + status, 1024 * 1024 - status);
        if (status != 0)
            die("didn't get EOF");
    } else if (strcmp(argv[2], "exit") == 0) {
        write(1, "Okay", strlen("Okay"));
    } else if (strcmp(argv[2], "close") == 0) {
        close(0);
        write(1, "Okay", strlen("Okay"));
    } else if (strcmp(argv[2], "nuls") == 0) {
        status = read(0, buffer, 1024 * 1024);
        if (status <= 0)
            sysdie("read failed");
        left = status;
        status = read(0, buffer + status, 1024 * 1024 - status);
        if (status != 0)
            die("didn't get EOF");
        if (left != 8 || memcmp(buffer, "T\0e\0s\0t\0", 8) != 0)
            die("got incorrect data");
        write(1, "Okay", strlen("Okay"));
    } else if (strcmp(argv[2], "large") == 0) {
        left = 1024 * 1024;
        status = 1;
        for (p = buffer; status > 0; p += status, left -= status) {
            do {
                status = read(0, p, left);
            } while (status == -1 && errno == EINTR);
            if (status < 0)
                break;
        }
        if (left != 0 || status != 0)
            die("did not read correct amount");
        for (i = 0; i < 1024 * 1024; i++)
            if (buffer[i] != 'A')
                die("invalid character in input");
        write(1, "Okay", strlen("Okay"));
    } else if (strcmp(argv[2], "delay") == 0) {
        left = 1024 * 1024;
        status = 1;
        for (p = buffer; status > 0; p += status, left -= status) {
            do {
                tv.tv_sec = 0;
                tv.tv_usec = 50000;
                select(0, NULL, NULL, NULL, &tv);
                status = read(0, p, left);
            } while (status == -1 && errno == EINTR);
            if (status < 0)
                break;
        }
        if (left != 0 || status != 0)
            die("did not read correct amount");
        for (i = 0; i < 1024 * 1024; i++)
            if (buffer[i] != 'A')
                die("invalid character in input");
        write(1, "Okay", strlen("Okay"));
    }
    return 0;
}
