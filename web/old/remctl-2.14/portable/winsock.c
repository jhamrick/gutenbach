/*
 * Supporting functions for the Windows socket API.
 *
 * Provides supporting functions and wrappers that help with portability to
 * the Windows socket API.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * This work is hereby placed in the public domain by its author.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/socket.h>


/*
 * Initializes the Windows socket library.  The returned parameter provides
 * information about the socket library, none of which we care about.  Return
 * true on success and false on failure.
 */
int
socket_init(void)
{
    WSADATA data;

    if (WSAStartup(MAKEWORD(2,2), &data))
        return 0;
    return 1;
}


/*
 * On Windows, strerror cannot be used for socket errors (or any other errors
 * over sys_nerr).  Try to use FormatMessage with a local static variable
 * instead.
 */
const char *
socket_strerror(err)
{
    const char *message = NULL;

    if (err >= sys_nerr) {
        char *p;
        DWORD f = FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM
            | FORMAT_MESSAGE_IGNORE_INSERTS;
        static char *buffer = NULL;

        if (buffer != NULL)
            LocalFree(buffer);
        if (FormatMessage(f, NULL, err, 0, (LPTSTR) &buffer, 0, NULL) != 0) {
            p = strchr(buffer, '\r');
            if (p != NULL)
                *p = '\0';
        }
        message = buffer;
    }
    if (message == NULL)
        message = strerror(err);
    return message;
}
