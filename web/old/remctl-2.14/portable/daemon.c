/*
 * Replacement for a missing daemon.
 *
 * Provides the same functionality as the library function daemon for those
 * systems that don't have it.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * This work is hereby placed in the public domain by its author.
 */

#include <config.h>
#include <portable/system.h>

#include <errno.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/stat.h>

/*
 * If we're running the test suite, rename daemon to avoid conflicts with the
 * system version.  #undef it first because some systems may define it to
 * another name.
 */
#if TESTING
# undef daemon
# define daemon test_daemon
int test_daemon(int, int);
#endif

int
daemon(int nochdir, int noclose)
{
    int status, fd;

    /*
     * Fork and exit in the parent to disassociate from the current process
     * group and become the leader of a new process group.
     */
    status = fork();
    if (status < 0)
        return -1;
    else if (status > 0)
        _exit(0);

    /*
     * setsid() should take care of disassociating from the controlling
     * terminal, and FreeBSD at least doesn't like TIOCNOTTY if you don't
     * already have a controlling terminal.  So only use the older TIOCNOTTY
     * method if setsid() isn't available.
     */
#if HAVE_SETSID
    if (setsid() < 0)
        return -1;
#elif defined(TIOCNOTTY)
    fd = open("/dev/tty", O_RDWR);
    if (fd >= 0) {
        if (ioctl(fd, TIOCNOTTY, NULL) < 0) {
            status = errno;
            close(fd);
            errno = status;
            return -1;
        }
        close(fd);
    }
#endif /* defined(TIOCNOTTY) */

    if (!nochdir && chdir("/") < 0)
        return -1;

    if (!noclose) {
        fd = open("/dev/null", O_RDWR, 0);
        if (fd < 0)
            return -1;
        else {
            if (dup2(fd, STDIN_FILENO) < 0)
                return -1;
            if (dup2(fd, STDOUT_FILENO) < 0)
                return -1;
            if (dup2(fd, STDERR_FILENO) < 0)
                return -1;
            if (fd > 2)
                close(fd);
        }
    }
    return 0;
}
