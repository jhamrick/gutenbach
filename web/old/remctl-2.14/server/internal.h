/*
 * Internal support functions for the remctld daemon.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2006, 2007, 2008, 2009
 *     Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#ifndef SERVER_INTERNAL_H
#define SERVER_INTERNAL_H 1

#include <config.h>
#include <portable/gssapi.h>
#include <portable/macros.h>
#include <portable/stdbool.h>

#include <util/util.h>

/* Forward declarations to avoid extra includes. */
struct iovec;

/*
 * Used as the default max buffer for the argv passed into the server, and for 
 * the return message from the server.
 */
#define MAXBUFFER       64000  

/*
 * The maximum size of argc passed to the server.  This is an arbitrary limit
 * to protect against memory-based denial of service attacks on the server.
 */
#define MAXCMDARGS      (4 * 1024)

BEGIN_DECLS

/* Holds the information about a client connection. */
struct client {
    int fd;                     /* File descriptor of client connection. */
    char *hostname;             /* Hostname of client (if available). */
    char *ipaddress;            /* IP address of client as a string. */
    int protocol;               /* Protocol version number. */
    gss_ctx_id_t context;       /* GSS-API context. */
    char *user;                 /* Name of the client as a string. */
    OM_uint32 flags;            /* Connection flags. */
    bool keepalive;             /* Whether keep-alive was set. */
    char *output;               /* Stores output to send to the client. */
    size_t outlen;              /* Length of output to send to client. */
    bool fatal;                 /* Whether a fatal error has occurred. */
};

/* Holds the configuration for a single command. */
struct confline {
    char *file;                 /* Config file name. */
    int lineno;                 /* Config file line number. */
    struct vector *line;        /* The split configuration line. */
    char *command;              /* Command (first argument). */
    char *subcommand;           /* Subcommand (second argument). */
    char *program;              /* Full file name of executable. */
    unsigned int *logmask;      /* Zero-terminated list of args to mask. */
    long stdin_arg;             /* Arg to pass on stdin, -1 for last. */
    char **acls;                /* Full file names of ACL files. */
};

/* Holds the complete parsed configuration for remctld. */
struct config {
    struct confline **rules;
    size_t count;
    size_t allocated;
};

/* Logging functions. */
void warn_gssapi(const char *, OM_uint32 major, OM_uint32 minor);
void warn_token(const char *, int status, OM_uint32 major, OM_uint32 minor);
void server_log_command(struct iovec **, struct confline *, const char *user);

/* Configuration file functions. */
struct config *server_config_load(const char *file);
void server_config_free(struct config *);
bool server_config_acl_permit(struct confline *, const char *user);
void server_config_set_gput_file(char *file);

/* Running commands. */
void server_run_command(struct client *, struct config *, struct iovec **);

/* Freeing the command structure. */
void server_free_command(struct iovec **);

/* Generic protocol functions. */
struct client *server_new_client(int fd, gss_cred_id_t creds);
void server_free_client(struct client *);
struct iovec **server_parse_command(struct client *, const char *, size_t);
bool server_send_error(struct client *, enum error_codes, const char *);

/* Protocol v1 functions. */
bool server_v1_send_output(struct client *, int status);
void server_v1_handle_commands(struct client *, struct config *);

/* Protocol v2 functions. */
bool server_v2_send_output(struct client *, int stream);
bool server_v2_send_status(struct client *, int);
bool server_v2_send_error(struct client *, enum error_codes, const char *);
void server_v2_handle_commands(struct client *, struct config *);

END_DECLS

#endif /* !SERVER_INTERNAL_H */
