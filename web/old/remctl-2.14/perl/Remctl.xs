/*
 * Perl bindings for the remctl client library.
 *
 * This is an XS source file, suitable for processing by xsubpp, that
 * generates Perl bindings for the libremctl client library.  It supports
 * both the simplified interface (via a simple remctl call) and the more
 * complex interface (returning a Net::Remctl object which is then used for
 * subsequent calls).
 *
 * The remctl opaque struct is mapped to a Net::Remctl object and supports
 * methods equivalent to the library functions prefixed by remctl_ that take
 * struct remctl * as their first argument.  remctl_new() is mapped to the
 * new method of the class.  remctl_output structs are returned as
 * Net::Remctl::Output objects with accessor functions that return the
 * elements of the remctl_output struct.  The types (output, status, error,
 * and done) are returned as lowercase strings rather than as numeric
 * constants.
 *
 * The simple interface is available via an exported remctl function which
 * returns a Net::Remctl::Result object with accessor functions for the
 * members of the struct.
 *
 * Written by Russ Allbery <rra@stanford.edu>
 * Copyright 2007, 2008 Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <EXTERN.h>
#include <perl.h>
#include <XSUB.h>

#include <errno.h>

#include <remctl.h>

/*
 * These typedefs are needed for xsubpp to work its magic with type
 * translation to Perl objects.
 */
typedef struct remctl *         Net__Remctl;
typedef struct remctl_result *  Net__Remctl__Result;
typedef struct remctl_output *  Net__Remctl__Output;

/* Map the remctl_output type constants to strings. */
const struct {
    enum remctl_output_type type;
    const char *name;
} OUTPUT_TYPE[] = {
    { REMCTL_OUT_OUTPUT, "output" },
    { REMCTL_OUT_STATUS, "status" },
    { REMCTL_OUT_ERROR,  "error"  },
    { REMCTL_OUT_DONE,   "done"   },
    { 0,                 NULL     }
};

/* XS code below this point. */

MODULE = Net::Remctl    PACKAGE = Net::Remctl   PREFIX = remctl_

PROTOTYPES: ENABLE

Net::Remctl::Result
remctl(host, port, principal, ...)
    const char *host
    unsigned short port
    const char *principal
  PREINIT:
    size_t count = items - 3;
    size_t i;
    const char **command;
  CODE:
    if (items <= 3)
        croak("Too few arguments to Net::Remctl::remctl");
    if (principal != NULL && *principal == '\0')
        principal = NULL;
    command = malloc(sizeof(char *) * (count + 1));
    if (command == NULL)
        croak("Error allocating memory in Net::Remctl::remctl: %s",
              strerror(errno));
    for (i = 0; i <= count; i++)
        command[i] = SvPV_nolen(ST(i + 3));
    command[count] = NULL;
    RETVAL = remctl(host, port, principal, command);
    if (RETVAL == NULL)
        croak("Error creating Net::Remctl::Result object: %s",
              strerror(errno));
    free(command);
  OUTPUT:
    RETVAL

Net::Remctl
remctl_new(class)
    const char *class
  CODE:
    RETVAL = remctl_new();
    if (RETVAL == NULL)
        croak("Error creating %s object: %s", class, strerror(errno));
  OUTPUT:
    RETVAL

void
DESTROY(self)
    Net::Remctl self
  CODE:
    if (self != NULL)
        remctl_close(self);

void
remctl_open(self, host, ...)
    Net::Remctl self
    const char *host
  PROTOTYPE: DISABLE
  PREINIT:
    size_t count = items - 2;
    unsigned short port = 0;
    const char *principal = NULL;
  PPCODE:
    if (count > 2)
        croak("Too many arguments to Net::Remctl::open");
    if (count >= 1)
        port = SvUV(ST(2));
    if (count >= 2 && ST(3) != &PL_sv_undef) {
        principal = SvPV_nolen(ST(3));
        if (*principal == '\0')
            principal = NULL;
    }
    if (remctl_open(self, host, port, principal))
        XSRETURN_YES;
    else
        XSRETURN_UNDEF;

void
remctl_command(self, ...)
    Net::Remctl self
  PREINIT:
    struct iovec *args;
    size_t count = items - 1;
    size_t i;
    int status;
  PPCODE:
    if (count == 0)
        croak("Too few arguments to Net::Remctl::command");
    args = malloc(sizeof(struct iovec) * count);
    if (args == NULL)
        croak("Error allocating memory in Net::Remctl::command: %s",
              strerror(errno));
    for (i = 1; i <= count; i++)
        args[i - 1].iov_base = SvPV(ST(i), args[i - 1].iov_len);
    status = remctl_commandv(self, args, count);
    free(args);
    if (status)
        XSRETURN_YES;
    else
        XSRETURN_UNDEF;

Net::Remctl::Output
remctl_output(self)
    Net::Remctl self

const char *
remctl_error(self)
    Net::Remctl self

MODULE = Net::Remctl    PACKAGE = Net::Remctl::Result

void
DESTROY(self)
    Net::Remctl::Result self
  CODE:
    remctl_result_free(self);

char *
error(self)
    Net::Remctl::Result self
  CODE:
    RETVAL = self->error;
  OUTPUT:
    RETVAL

SV *
stdout(self)
    Net::Remctl::Result self
  CODE:
    if (self->stdout_buf == NULL)
        XSRETURN_UNDEF;
    else
        RETVAL = newSVpvn(self->stdout_buf, self->stdout_len);
  OUTPUT:
    RETVAL

SV *
stderr(self)
    Net::Remctl::Result self
  CODE:
    if (self->stderr_buf == NULL)
        XSRETURN_UNDEF;
    else
        RETVAL = newSVpvn(self->stderr_buf, self->stderr_len);
  OUTPUT:
    RETVAL

int
status(self)
    Net::Remctl::Result self
  CODE:
    RETVAL = self->status;
  OUTPUT:
    RETVAL

MODULE = Net::Remctl    PACKAGE = Net::Remctl::Output

const char *
type(self)
    Net::Remctl::Output self
  PREINIT:
    size_t i;
  CODE:
    RETVAL = NULL;
    for (i = 0; OUTPUT_TYPE[i].name != NULL; i++)
        if (OUTPUT_TYPE[i].type == self->type) {
            RETVAL = OUTPUT_TYPE[self->type].name;
            break;
        }
  OUTPUT:
    RETVAL

SV *
data(self)
    Net::Remctl::Output self
  CODE:
    if (self->data == NULL)
        XSRETURN_UNDEF;
    else
        RETVAL = newSVpvn(self->data, self->length);
  OUTPUT:
    RETVAL

size_t
length(self)
    Net::Remctl::Output self
  CODE:
    RETVAL = self->length;
  OUTPUT:
    RETVAL

int
stream(self)
    Net::Remctl::Output self
  CODE:
    RETVAL = self->stream;
  OUTPUT:
    RETVAL

int
status(self)
    Net::Remctl::Output self
  CODE:
    RETVAL = self->status;
  OUTPUT:
    RETVAL

int
error(self)
    Net::Remctl::Output self
  CODE:
    RETVAL = self->error;
  OUTPUT:
    RETVAL
