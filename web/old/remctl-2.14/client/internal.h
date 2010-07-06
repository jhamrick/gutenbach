/*
 * Internal support functions for the remctl client library.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Based on prior work by Anton Ushakov
 * Copyright 2002, 2003, 2004, 2005, 2006, 2007, 2008
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#ifndef CLIENT_INTERNAL_H
#define CLIENT_INTERNAL_H 1

#include <config.h>
#include <portable/gssapi.h>
#include <portable/macros.h>
#include <portable/stdbool.h>

/* Forward declaration to avoid unnecessary includes. */
struct iovec;

BEGIN_DECLS

/* Private structure that holds the details of an open remctl connection. */
struct remctl {
    const char *host;           /* From remctl_open, stored here because */
    unsigned short port;        /*   remctl v1 requires opening a new    */
    const char *principal;      /*   connection for each command.        */
    int protocol;               /* Protocol version. */
    int fd;
    gss_ctx_id_t context;
    char *error;
    struct remctl_output *output;
    int status;
    bool ready;                 /* If true, we are expecting server output. */
};

/* Internal functions should all default to hidden visibility. */
#pragma GCC visibility push(hidden)

/* Helper functions to set errors. */
void internal_set_error(struct remctl *, const char *, ...);
void internal_gssapi_error(struct remctl *, const char *error,
                           OM_uint32 major, OM_uint32 minor);
void internal_token_error(struct remctl *, const char *error, int status,
                          OM_uint32 major, OM_uint32 minor);

/* Wipe and free the output token. */
void internal_output_wipe(struct remctl_output *);

/* General connection opening and negotiation function. */
bool internal_open(struct remctl *, const char *host, unsigned short port,
                   const char *principal);

/* Send a protocol v1 command. */
bool internal_v1_commandv(struct remctl *, const struct iovec *command,
                          size_t count);

/* Read a protocol v1 response. */
struct remctl_output *internal_v1_output(struct remctl *);

/* Send a protocol v2 command. */
bool internal_v2_commandv(struct remctl *, const struct iovec *command,
                          size_t count);

/* Send a protocol v2 QUIT command. */
bool internal_v2_quit(struct remctl *);

/* Read a protocol v2 response. */
struct remctl_output *internal_v2_output(struct remctl *);

/* Undo default visibility change. */
#pragma GCC visibility pop

END_DECLS

#endif /* !CLIENT_INTERNAL_H */
