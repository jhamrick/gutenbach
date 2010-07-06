/*
 * Set or clear file descriptor flags.
 *
 * Simple functions (wrappers around fcntl) to set or clear file descriptor
 * flags like close-on-exec or nonblocking I/O.
 *
 * Copyright 2008 Board of Trustees, Leland Stanford Jr. University
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
#ifndef O_NONBLOCK
# include <sys/ioctl.h>
# if HAVE_SYS_FILIO_H
#  include <sys/filio.h>
# endif
#endif

#include <util/util.h>


/*
 * Set a file to close-on-exec (or clear that setting if the flag is false),
 * returning true on success and false on failure.
 *
 * One is supposed to retrieve the flags, add FD_CLOEXEC, and then set them,
 * although I've never seen a system with any flags other than close-on-exec.
 * Do it right anyway; it's not that expensive.
*/
bool
fdflag_close_exec(int fd, bool flag)
{
    int oflag, mode;

    oflag = fcntl(fd, F_GETFD, 0);
    if (oflag < 0)
        return false;
    mode = flag ? (oflag | FD_CLOEXEC) : (oflag & ~FD_CLOEXEC);
    return (fcntl(fd, F_SETFD, mode) == 0);
}


/*
 * Set a file descriptor to nonblocking (or clear the nonblocking flag if flag
 * is false), returning true on success and false on failure.
 *
 * Always use O_NONBLOCK; O_NDELAY is not the same thing historically.  The
 * semantics of O_NDELAY are that if the read would block, it returns 0
 * instead.  This is indistinguishable from an end of file condition.  POSIX
 * added O_NONBLOCK, which requires read to return -1 and set errno to EAGAIN,
 * which is what we want.
 *
 * FNDELAY (4.3BSD) originally did the correct thing, although it has a
 * different incompatibility (affecting all users of a socket rather than just
 * a file descriptor and returning EWOULDBLOCK instead of EAGAIN) that we
 * probably don't care about.  Using it is probably safe, but BSD should also
 * have the ioctl, and at least on Solaris FNDELAY does the same thing as
 * O_NDELAY, not O_NONBLOCK.  So if we don't have O_NONBLOCK, fall back to the
 * ioctl instead.
 *
 * Reference:  Stevens, Advanced Unix Programming, pg. 364.
 *
 * Note that O_NONBLOCK is known not to work on earlier versions of ULTRIX,
 * SunOS, and AIX, possibly not setting the socket nonblocking at all, despite
 * the fact that they do define it.  It works in later SunOS and, current AIX,
 * however, and a 1999-10-25 survey of current operating systems failed to
 * turn up any that didn't handle it correctly (as required by POSIX), while
 * HP-UX 11.00 did use the broken return-zero semantics of O_NDELAY (most
 * other operating systems surveyed treated O_NDELAY as synonymous with
 * O_NONBLOCK).  Accordingly, we currently unconditionally use O_NONBLOCK.  If
 * this causes too many problems, an autoconf test may be required.
 */
#ifdef O_NONBLOCK
bool
fdflag_nonblocking(int fd, bool flag)
{
    int mode;

    mode = fcntl(fd, F_GETFL, 0);
    if (mode < 0)
        return false;
    mode = (flag ? (mode | O_NONBLOCK) : (mode & ~O_NONBLOCK));
    return (fcntl(fd, F_SETFL, mode) == 0);
}
#else /* !O_NONBLOCK */
int
nonblocking(int fd, bool flag)
{
    int state;

    state = flag ? 1 : 0;
    return ioctl(fd, FIONBIO, &state);
}
#endif /* !O_NONBLOCK */
