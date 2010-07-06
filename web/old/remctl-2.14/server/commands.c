/*
 * Running commands.
 *
 * These are the functions for running external commands under remctld and
 * calling the appropriate protocol functions to deal with the output.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Based on work by Anton Ushakov
 * Copyright 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>
#include <portable/system.h>
#include <portable/uio.h>

#include <errno.h>
#include <fcntl.h>
#ifdef HAVE_SYS_SELECT_H
# include <sys/select.h>
#endif
#include <sys/time.h>
#include <sys/wait.h>

#include <server/internal.h>
#include <util/util.h>

/* Data structure used to hold details about a running process. */
struct process {
    bool reaped;                /* Whether we've reaped the process. */
    int fds[2];                 /* Array of file descriptors for output. */
    int stdin_fd;               /* File descriptor for standard input. */
    struct iovec *input;        /* Data to pass on standard input. */
    pid_t pid;                  /* Process ID of child. */
    int status;                 /* Exit status. */
};


/*
 * Processes the input to and output from an external program.  Takes the
 * client struct and a struct representing the running process.  Feeds input
 * data to the process on standard input and reads from all the streams as
 * output is available, stopping when they all reach EOF.
 *
 * For protocol v2 and higher, we can send the output immediately as we get
 * it.  For protocol v1, we instead accumulate the output in the buffer stored
 * in our client struct, and will send it out later in conjunction with the
 * exit status.
 *
 * Returns true on success, false on failure.
 */
static int
server_process_output(struct client *client, struct process *process)
{
    char junk[BUFSIZ];
    char *p;
    size_t offset = 0;
    size_t left = MAXBUFFER;
    ssize_t status[2], instatus;
    int i, maxfd, fd, result;
    fd_set readfds, writefds;
    struct timeval timeout;

    /* If we haven't allocated an output buffer, do so now. */
    if (client->output == NULL)
        client->output = xmalloc(MAXBUFFER);
    p = client->output;

    /*
     * Initialize read status for standard output and standard error and write
     * status for standard input to the process.  Non-zero says that we keep
     * trying to read or write.
     */
    status[0] = -1;
    status[1] = -1;
    instatus = (process->input != NULL ? -1 : 0);

    /*
     * Now, loop while we have input.  We no longer have input if the return
     * status of read is 0 on all file descriptors.  At that point, we break
     * out of the loop.
     *
     * Exceptionally, however, we want to catch the case where our child
     * process ran some other command that didn't close its inherited standard
     * output and error and then exited itself.  This is not uncommon with
     * init scripts that start poorly-written daemons.  Once our child process
     * is finished, we're done, even if standard output and error from the
     * child process aren't closed yet.  To catch this case, call waitpid with
     * the WNOHANG flag each time through the select loop and decide we're
     * done as soon as our child has exited.
     *
     * Meanwhile, if we have input data, then as long as we've not gotten an
     * EPIPE error from sending input data to the process we keep writing
     * input data as select indicates the process can receive it.  However, we
     * don't care if we've sent all input data before the process says it's
     * done and exits.
     */
    while (!process->reaped) {
        FD_ZERO(&readfds);
        maxfd = -1;
        for (i = 0; i < 2; i++) {
            if (status[i] != 0) {
                if (process->fds[i] > maxfd)
                    maxfd = process->fds[i];
                FD_SET(process->fds[i], &readfds);
            }
        }
        if (instatus != 0) {
            FD_ZERO(&writefds);
            if (process->stdin_fd > maxfd)
                maxfd = process->stdin_fd;
            FD_SET(process->stdin_fd, &writefds);
        }
        if (maxfd == -1)
            break;

        /*
         * We want to wait until either our child exits or until we get data
         * on its output file descriptors.  Normally, the SIGCHLD signal from
         * the child exiting would break us out of our select loop.  However,
         * the child could exit between the waitpid call and the select call,
         * in which case select could block forever since there's nothing to
         * wake it up.
         *
         * The POSIX-correct way of doing this is to block SIGCHLD and then
         * use pselect instead of select with a signal mask that allows
         * SIGCHLD.  This allows SIGCHLD from the exiting child process to
         * reliably interrupt pselect without race conditions from the child
         * exiting before pselect is called.
         *
         * Unfortunately, Linux didn't implement a proper pselect until 2.6.16
         * and the glibc wrapper that emulates it leaves us open to exactly
         * the race condition we're trying to avoid.  This unfortunately
         * leaves us with no choice but to set a timeout and wake up every
         * five seconds to see if our child died.  (The wait time is arbitrary
         * but makes the test suite less annoying.)
         *
         * If we see that the child has already exited, do one final poll of
         * our output file descriptors and then call the command finished.
         */
        timeout.tv_sec = 5;
        timeout.tv_usec = 0;
        if (waitpid(process->pid, &process->status, WNOHANG) > 0) {
            process->reaped = true;
            timeout.tv_sec = 0;
        }
        if (instatus != 0)
            result = select(maxfd + 1, &readfds, &writefds, NULL, &timeout);
        else
            result = select(maxfd + 1, &readfds, NULL, NULL, &timeout);
        if (result < 0 && errno != EINTR) {
            syswarn("select failed");
            server_send_error(client, ERROR_INTERNAL, "Internal failure");
            goto fail;
        }

        /*
         * If we can still write and our child selected for writing, send as
         * much data as we can.
         */
        if (instatus != 0 && FD_ISSET(process->stdin_fd, &writefds)) {
            instatus = write(process->stdin_fd,
                             (char *) process->input->iov_base + offset,
                             process->input->iov_len - offset);
            if (instatus < 0) {
                if (errno == EPIPE)
                    instatus = 0;
                else if (errno != EINTR && errno != EAGAIN) {
                    syswarn("write failed");
                    server_send_error(client, ERROR_INTERNAL,
                                      "Internal failure");
                    goto fail;
                }
            }
            offset += instatus;
            if (offset >= process->input->iov_len) {
                close(process->stdin_fd);
                instatus = 0;
            }
        }

        /*
         * Iterate through each set file descriptor and read its output.  If
         * we're using protocol version one, we append all the output together
         * into the buffer.  Otherwise, we send an output token for each bit
         * of output as we see it.
         */
        for (i = 0; i < 2; i++) {
            fd = process->fds[i];
            if (!FD_ISSET(fd, &readfds))
                continue;
            if (client->protocol == 1) {
                if (left > 0) {
                    status[i] = read(fd, p, left);
                    if (status[i] < 0 && (errno != EINTR && errno != EAGAIN))
                        goto readfail;
                    else if (status[i] > 0) {
                        p += status[i];
                        left -= status[i];
                    }
                } else {
                    status[i] = read(fd, junk, sizeof(junk));
                    if (status[i] < 0 && (errno != EINTR && errno != EAGAIN))
                        goto readfail;
                }
            } else {
                status[i] = read(fd, client->output, MAXBUFFER);
                if (status[i] < 0 && (errno != EINTR && errno != EAGAIN))
                    goto readfail;
                if (status[i] > 0) {
                    client->outlen = status[i];
                    if (!server_v2_send_output(client, i + 1))
                        goto fail;
                }
            }
        }
    }
    if (client->protocol == 1)
        client->outlen = p - client->output;
    return 1;

readfail:
    syswarn("read failed");
    server_send_error(client, ERROR_INTERNAL, "Internal failure");
fail:
    return 0;
}


/*
 * Process an incoming command.  Check the configuration files and the ACL
 * file, and if appropriate, forks off the command.  Takes the argument vector
 * and the user principal, and a buffer into which to put the output from the
 * executable or any error message.  Returns 0 on success and a negative
 * integer on failure.
 *
 * Using the command and the subcommand, the following argument, a lookup in
 * the conf data structure is done to find the command executable and acl
 * file.  If the conf file, and subsequently the conf data structure contains
 * an entry for this command with subcommand equal to "ALL", that is a
 * wildcard match for any given subcommand.  The first argument is then
 * replaced with the actual program name to be executed.
 *
 * After checking the acl permissions, the process forks and the child execv's
 * the command with pipes arranged to gather output. The parent waits for the
 * return code and gathers stdout and stderr pipes.
 */
void
server_run_command(struct client *client, struct config *config,
                   struct iovec **argv)
{
    char *program;
    char *path = NULL;
    char *command = NULL;
    char *subcommand = NULL;
    struct confline *cline = NULL;
    int stdin_pipe[2], stdout_pipe[2], stderr_pipe[2];
    char **req_argv = NULL;
    size_t count, i, j, stdin_arg;
    bool ok;
    int fd;
    struct process process = { 0, { 0, 0 }, 0, NULL, -1, 0 };
    const char *user = client->user;

    /*
     * We need at least one argument.  This is also rejected earlier when
     * parsing the command and checking argc, but may as well be sure.
     */
    if (argv[0] == NULL) {
        notice("empty command from user %s", user);
        server_send_error(client, ERROR_BAD_COMMAND, "Invalid command token");
        goto done;
    }

    /*
     * Neither the command nor the subcommand may ever contain nuls.
     * Arguments may only contain nuls if they're the argument being passed on
     * standard input.
     */
    for (i = 0; argv[i] != NULL && i < 2; i++) {
        if (memchr(argv[i]->iov_base, '\0', argv[i]->iov_len)) {
            notice("%s from user %s contains nul octet",
                   (i == 0) ? "command" : "subcommand", user);
            server_send_error(client, ERROR_BAD_COMMAND,
                              "Invalid command token");
            goto done;
        }
    }

    /* We need the command and subcommand as nul-terminated strings. */
    command = xstrndup(argv[0]->iov_base, argv[0]->iov_len);
    if (argv[1] != NULL)
        subcommand = xstrndup(argv[1]->iov_base, argv[1]->iov_len);

    /*
     * Look up the command and the ACL file from the conf file structure in
     * memory.  Commands with no subcommand argument will only match lines
     * with the ALL wildcard.
     */
    for (i = 0; i < config->count; i++) {
        cline = config->rules[i];
        if (strcmp(cline->command, command) == 0) {
            if (strcmp(cline->subcommand, "ALL") == 0
                || (subcommand != NULL
                    && strcmp(cline->subcommand, subcommand) == 0)) {
                path = cline->program;
                break;
            }
        }
    }

    /*
     * Arguments may only contain nuls if they're the argument being passed on
     * standard input.
     */
    for (i = 1; argv[i] != NULL; i++) {
        if ((long) i == cline->stdin_arg)
            continue;
        if (argv[i + 1] == NULL && cline->stdin_arg == -1)
            continue;
        if (memchr(argv[i]->iov_base, '\0', argv[i]->iov_len)) {
            notice("argument %d from user %s contains nul octet", i, user);
            server_send_error(client, ERROR_BAD_COMMAND,
                              "Invalid command token");
            goto done;
        }
    }

    /* Log after we look for command so we can get potentially get logmask. */
    server_log_command(argv, path == NULL ? NULL : cline, user);

    /*
     * Check the command, aclfile, and the authorization of this client to
     * run this command.
     */
    if (path == NULL) {
        notice("unknown command %s%s%s from user %s", command,
               (subcommand == NULL) ? "" : " ",
               (subcommand == NULL) ? "" : subcommand, user);
        server_send_error(client, ERROR_UNKNOWN_COMMAND, "Unknown command");
        goto done;
    }
    if (!server_config_acl_permit(cline, user)) {
        notice("access denied: user %s, command %s%s%s", user, command,
               (subcommand == NULL) ? "" : " ",
               (subcommand == NULL) ? "" : subcommand);
        server_send_error(client, ERROR_ACCESS, "Access denied");
        goto done;
    }

    /* Get ready to assemble the argv of the command. */
    for (count = 0; argv[count] != NULL; count++)
        ;
    req_argv = xmalloc((count + 1) * sizeof(char *));

    /*
     * Get the real program name, and use it as the first argument in argv
     * passed to the command.  Then build the rest of the argv for the
     * command, splicing out the argument we're passing on stdin (if any).
     */
    program = strrchr(path, '/');
    if (program == NULL)
        program = path;
    else
        program++;
    req_argv[0] = program;
    if (cline->stdin_arg == -1)
        stdin_arg = count - 1;
    else
        stdin_arg = (size_t) cline->stdin_arg;
    for (i = 1, j = 1; i < count; i++) {
        if (i == stdin_arg) {
            process.input = argv[i];
            continue;
        }
        if (argv[i]->iov_len == 0)
            req_argv[j] = xstrdup("");
        else
            req_argv[j] = xstrndup(argv[i]->iov_base, argv[i]->iov_len);
        j++;
    }
    req_argv[j] = NULL;

    /*
     * These pipes are used for communication with the child process that 
     * actually runs the command.
     */
    if (pipe(stdout_pipe) != 0 || pipe(stderr_pipe) != 0) {
        syswarn("cannot create pipes");
        server_send_error(client, ERROR_INTERNAL, "Internal failure");
        goto done;
    }
    if (process.input != NULL && pipe(stdin_pipe) != 0) {
        syswarn("cannot create stdin pipe");
        server_send_error(client, ERROR_INTERNAL, "Internal failure");
        goto done;
    }

    /*
     * Flush output before forking, mostly in case -S was given and we've
     * therefore been writing log messages to standard output that may not
     * have been flushed yet.
     */
    fflush(stdout);
    process.pid = fork();
    switch (process.pid) {
    case -1:
        syswarn("cannot fork");
        server_send_error(client, ERROR_INTERNAL, "Internal failure");
        goto done;

    /* In the child. */
    case 0:
        dup2(stdout_pipe[1], 1);
        close(stdout_pipe[0]);
        close(stdout_pipe[1]);
        dup2(stderr_pipe[1], 2);
        close(stderr_pipe[0]);
        close(stderr_pipe[1]);

        /*
         * Set up stdin pipe if we have input data.
         *
         * If we don't have input data, child doesn't need stdin at all, but
         * just closing it causes problems for puppet.  Reopen on /dev/null
         * instead.  Ignore failure here, since it probably won't matter and
         * worst case is that we leave stdin closed.
         */
        if (process.input != NULL) {
            dup2(stdin_pipe[0], 0);
            close(stdin_pipe[0]);
            close(stdin_pipe[1]);
        } else {
            close(0);
            fd = open("/dev/null", O_RDONLY);
            if (fd > 0) {
                dup2(fd, 0);
                close(fd);
            }
        }

        /*
         * Older versions of MIT Kerberos left the replay cache file open
         * across exec.  Newer versions correctly set it close-on-exec, but
         * close our low-numbered file descriptors anyway for older versions.
         * We're just trying to get the replay cache, so we don't have to go
         * very high.
         */
        for (fd = 3; fd < 16; fd++)
            close(fd);

        /*
         * Put the authenticated principal and other connection information in
         * the environment.  REMUSER is for backwards compatibility with
         * earlier versions of remctl.
         */
        if (setenv("REMUSER", client->user, 1) < 0) {
            syswarn("cannot set REMUSER in environment");
            exit(-1);
        }
        if (setenv("REMOTE_USER", client->user, 1) < 0) {
            syswarn("cannot set REMOTE_USER in environment");
            exit(-1);
        }
        if (setenv("REMOTE_ADDR", client->ipaddress, 1) < 0) {
            syswarn("cannot set REMOTE_ADDR in environment");
            exit(-1);
        }
        if (client->hostname != NULL) {
            if (setenv("REMOTE_HOST", client->hostname, 1) < 0) {
                syswarn("cannot set REMOTE_HOST in environment");
                exit(-1);
            }
        }

        /* Run the command. */
        execv(path, req_argv);

        /*
         * This happens only if the exec fails.  Print out an error message to
         * the stderr pipe and fail; that's the best that we can do.
         */
        fprintf(stderr, "Cannot execute: %s\n", strerror(errno));
        exit(-1);

    /* In the parent. */
    default:
        close(stdout_pipe[1]);
        close(stderr_pipe[1]);
        if (process.input != NULL)
            close(stdin_pipe[0]);

        /*
         * Unblock the read ends of the output pipes, to enable us to read
         * from both iteratively, and unblock the write end of the input pipe
         * if we have one so that we don't block when feeding data to our
         * child.
         */
        fdflag_nonblocking(stdout_pipe[0], true);
        fdflag_nonblocking(stderr_pipe[0], true);
        if (process.input != NULL)
            fdflag_nonblocking(stdin_pipe[1], true);

        /*
         * This collects output from both pipes iteratively, while the child
         * is executing, and processes it.  It also sends input data if we
         * have any.
         */
        process.fds[0] = stdout_pipe[0];
        process.fds[1] = stderr_pipe[0];
        if (process.input != NULL)
            process.stdin_fd = stdin_pipe[1];
        ok = server_process_output(client, &process);
        close(process.fds[0]);
        close(process.fds[1]);
        if (process.input != NULL)
            close(process.stdin_fd);
        if (!process.reaped)
            waitpid(process.pid, &process.status, 0);
        if (WIFEXITED(process.status))
            process.status = (signed int) WEXITSTATUS(process.status);
        else
            process.status = -1;
        if (ok) {
            if (client->protocol == 1)
                server_v1_send_output(client, process.status);
            else
                server_v2_send_status(client, process.status);
        }
    }

 done:
    if (command != NULL)
        free(command);
    if (subcommand != NULL)
        free(subcommand);
    if (req_argv != NULL) {
        i = 1;
        while (req_argv[i] != NULL) {
            free(req_argv[i]);
            i++;
        }
        free(req_argv);
    }
}


/*
 * Free a command, represented as a NULL-terminated array of pointers to iovec
 * structs.
 */
void
server_free_command(struct iovec **command)
{
    struct iovec **arg;

    for (arg = command; *arg != NULL; arg++) {
        if ((*arg)->iov_base != NULL)
            free((*arg)->iov_base);
        free(*arg);
    }
    free(command);
}
