/*
 * remctl PECL extension for PHP
 *
 * Provides bindings for PHP very similar to the libremctl library for C or
 * the Net::Remctl bindings for Perl.
 *
 * Originally written by Andrew Mortensen <admorten@umich.edu>, 2008
 * Copyright 2008 Andrew Mortensen <admorten@umich.edu>
 * Copyright 2008 Board of Trustees, Leland Stanford Jr. University
 *
 * See LICENSE for licensing terms.
 */

#include <config.h>

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>

#include <client/remctl.h>

#include <php.h>
#include <php_remctl.h>

static int le_remctl_internal;

static zend_function_entry remctl_functions[] = {
    ZEND_FE(remctl,         NULL)
    ZEND_FE(remctl_new,     NULL)
    ZEND_FE(remctl_open,    NULL)
    ZEND_FE(remctl_close,   NULL)
    ZEND_FE(remctl_command, NULL)
    ZEND_FE(remctl_output,  NULL)
    ZEND_FE(remctl_error,   NULL)
    { NULL, NULL, NULL, 0, 0 }
};

zend_module_entry remctl_module_entry = {
    STANDARD_MODULE_HEADER,
    PHP_REMCTL_EXTNAME,
    remctl_functions,
    PHP_MINIT(remctl),
    NULL,
    NULL,
    NULL,
    NULL,
    PHP_REMCTL_VERSION,
    STANDARD_MODULE_PROPERTIES
};

#ifdef COMPILE_DL_REMCTL
ZEND_GET_MODULE(remctl)
#endif

/*
 * Destructor for a remctl object.  Close the underlying connection.
 */
static void
php_remctl_dtor(zend_rsrc_list_entry *rsrc TSRMLS_DC)
{
    struct remctl *r = (struct remctl *) rsrc->ptr;

    if (r != NULL)
        remctl_close(r);
}


/*
 * Initialize the module and register the destructor.  Stores the resource
 * number of the module in le_remctl_internal.
 */
PHP_MINIT_FUNCTION(remctl)
{
    le_remctl_internal =
        zend_register_list_destructors_ex(php_remctl_dtor, NULL,
            PHP_REMCTL_RES_NAME, module_number);
    return SUCCESS;
}


/*
 * The simplified interface.  Make a call and return the results as an
 * object.
 */
ZEND_FUNCTION(remctl)
{
    zval *cmd_array, **data;
    void **data_ref;
    HashTable *hash;
    HashPosition pos;
    char *host, *principal = NULL;
    const char **command = NULL;
    long port;
    int hlen, plen, count, i, status;
    int success = 0;
    struct remctl_result *result = NULL;

    /*
     * Read the arguments (host, port, principal, and command) and check their
     * validity.  Host and command are required, so all arguments must be
     * provided, but an empty string can be passed in as the principal.
     */
    status = zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "slsa", &host,
                 &hlen, &port, &principal, &plen, &cmd_array);
    if (status == FAILURE) {
        zend_error(E_WARNING, "remctl: invalid parameters\n");
        RETURN_NULL();
    }
    if (hlen == 0) {
        zend_error(E_WARNING, "remctl: host must be a valid string\n");
        RETURN_NULL();
    }
    if (plen == 0)
        principal = NULL;
    hash = Z_ARRVAL_P(cmd_array);
    count = zend_hash_num_elements(hash);
    if (count < 1) {
        zend_error(E_WARNING, "remctl: command must not be empty\n");
        RETURN_NULL();
    }

    /*
     * Convert the command array into the char ** needed by libremctl.  This
     * is less than ideal because we make another copy of all of the
     * arguments.  There should be some way to do this without making a copy.
     */
    command = emalloc((count + 1) * sizeof(char *));
    if (command == NULL) {
        zend_error(E_WARNING, "remctl: emalloc failed\n");
        RETURN_NULL();
    }
    i = 0;
    zend_hash_internal_pointer_reset_ex(hash, &pos);
    data_ref = (void **) &data;
    while (zend_hash_get_current_data_ex(hash, data_ref, &pos) == SUCCESS) {
        if (Z_TYPE_PP(data) != IS_STRING) {
            zend_error(E_WARNING, "remctl: command contains non-string\n");
            goto cleanup;
        }
        if (i >= count) {
            zend_error(E_WARNING, "remctl: internal error: incorrect count\n");
            goto cleanup;
        }
        command[i] = estrndup(Z_STRVAL_PP(data), Z_STRLEN_PP(data));
        if (command[i] == NULL) {
            zend_error(E_WARNING, "remctl: estrndup failed\n");
            count = i;
            goto cleanup;
        }
        i++;
        zend_hash_move_forward_ex(hash, &pos);
    }
    command[count] = NULL;

    /* Run the actual remctl call. */
    result = remctl(host, port, principal, command);
    if (result == NULL) {
        zend_error(E_WARNING, "remctl: %s\n", strerror(errno));
        goto cleanup;
    }

    /*
     * Convert the remctl result to an object.  return_value is defined for us
     * by Zend.
     */
    if (object_init(return_value) != SUCCESS) {
        zend_error(E_WARNING, "remctl: object_init failed\n");
        goto cleanup;
    }
    if (result->error == NULL)
        add_property_string(return_value, "error", "", 1);
    else
        add_property_string(return_value, "error", result->error, 1);
    add_property_stringl(return_value, "stdout", result->stdout_buf,
        result->stdout_len, 1);
    add_property_long(return_value, "stdout_len", result->stdout_len);
    add_property_stringl(return_value, "stderr", result->stderr_buf,
        result->stderr_len, 1);
    add_property_long(return_value, "stderr_len", result->stderr_len);
    add_property_long(return_value, "status", result->status);
    success = 1;

cleanup:
    if (command != NULL) {
        for (i = 0; i < count; i++)
            efree((char *) command[i]);
        efree(command);
    }
    if (result != NULL)
        remctl_result_free(result);
    if (!success)
        RETURN_NULL();
}


/*
 * Now the full interface.  First, the constructor.
 */
ZEND_FUNCTION(remctl_new)
{
    struct remctl *r;

    r = remctl_new();
    if (r == NULL) {
        zend_error(E_WARNING, "remctl_new: %s", strerror(errno));
        RETURN_NULL();
    }
    ZEND_REGISTER_RESOURCE(return_value, r, le_remctl_internal);
}


/*
 * Open a connection to the remote host.  Only the host parameter is required;
 * the rest are optional.  PHP may require something be passed in for
 * principal, but the empty string is taken to mean "use the library default."
 */
ZEND_FUNCTION(remctl_open)
{
    struct remctl *r;
    zval *zrem;
    char *host;
    char *principal = NULL;
    long port = 0;
    int hlen, plen, status;

    /* Parse and verify arguments. */
    status = zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "rs|ls", &zrem,
                 &host, &hlen, &port, &principal, &plen);
    if (status == FAILURE) {
        zend_error(E_WARNING, "remctl_open: invalid parameters\n");
        RETURN_FALSE;
    }
    if (plen == 0)
        principal = NULL;
    ZEND_FETCH_RESOURCE(r, struct remctl *, &zrem, -1, PHP_REMCTL_RES_NAME,
        le_remctl_internal);

    /* Now we have all the arguments and can do the real work. */
    if (!remctl_open(r, host, port, principal))
        RETURN_FALSE;
    RETURN_TRUE;
}


/*
 * Send a command to the remote server.
 */
ZEND_FUNCTION(remctl_command)
{
    struct remctl *r;
    zval *zrem, *cmd_array, **data;
    void **data_ref;
    HashTable *hash;
    HashPosition pos;
    struct iovec *cmd_vec = NULL;
    int i, count, status;
    int success = 0;

    /* Parse and verify arguments. */
    status = zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "ra", &zrem,
                 &cmd_array);
    if (status == FAILURE) {
        zend_error(E_WARNING, "remctl_command: invalid parameters\n");
        RETURN_FALSE;
    }
    ZEND_FETCH_RESOURCE(r, struct remctl *, &zrem, -1, PHP_REMCTL_RES_NAME,
        le_remctl_internal);
    hash = Z_ARRVAL_P(cmd_array);
    count = zend_hash_num_elements(hash);
    if (count < 1) {
        zend_error(E_WARNING, "remctl_command: command must not be empty\n");
        RETURN_NULL();
    }

    /*
     * Transform the PHP array into an array of struct iovec.  This is less
     * than ideal because it makes another copy of all of the data.  There
     * should be some way to do this without copying.
     */
    cmd_vec = emalloc(count * sizeof(struct iovec));
    if (cmd_vec == NULL) {
        zend_error(E_WARNING, "remctl_command: emalloc failed\n");
        RETURN_FALSE;
    }
    i = 0;
    zend_hash_internal_pointer_reset_ex(hash, &pos);
    data_ref = (void **) &data;
    while (zend_hash_get_current_data_ex(hash, data_ref, &pos) == SUCCESS) {
        if (Z_TYPE_PP(data) != IS_STRING) {
            zend_error(E_WARNING,
                "remctl_command: command contains non-string\n");
            goto cleanup;
        }
        if (i >= count) {
            zend_error(E_WARNING,
                "remctl_command: internal error: incorrect count\n");
            goto cleanup;
        }
        cmd_vec[i].iov_base = emalloc(Z_STRLEN_PP(data) + 1);
        if (cmd_vec[i].iov_base == NULL) {
            zend_error(E_WARNING, "remctl_command: emalloc failed\n");
            count = i;
            goto cleanup;
        }
        cmd_vec[i].iov_len = Z_STRLEN_PP(data);
        memcpy(cmd_vec[i].iov_base, Z_STRVAL_PP(data), cmd_vec[i].iov_len);
        i++;
        zend_hash_move_forward_ex(hash, &pos);
    }

    /* Finally, we can do the work. */
    if (!remctl_commandv(r, cmd_vec, count))
        goto cleanup;
    success = 1;

cleanup:
    if (cmd_vec != NULL) {
        for (i = 0; i < count; i++)
            efree(cmd_vec[i].iov_base);
        efree(cmd_vec);
    }
    if (!success)
        RETURN_FALSE;
    RETURN_TRUE;
}


/*
 * Get an output token from the server and return it as an object.
 */
ZEND_FUNCTION(remctl_output)
{
    struct remctl *r;
    struct remctl_output *output;
    zval *zrem;
    int status;

    /* Parse and verify arguments. */
    status = zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "r", &zrem);
    if (status == FAILURE) {
        zend_error(E_WARNING, "remctl_output: invalid parameters\n");
        RETURN_NULL();
    }
    ZEND_FETCH_RESOURCE(r, struct remctl *, &zrem, -1, PHP_REMCTL_RES_NAME,
        le_remctl_internal);

    /* Get the output token. */
    output = remctl_output(r);
    if (output == NULL) {
        zend_error(E_WARNING, "remctl_output: error reading from server: %s",
            remctl_error(r));
        RETURN_NULL();
    }

    /*
     * Populate an object with the output results.  return_value is defined
     * for us by Zend.
     */
    if (object_init(return_value) != SUCCESS) {
        zend_error(E_WARNING, "remctl_output: object_init failed\n");
        RETURN_NULL();
    }
    switch (output->type) {
    case REMCTL_OUT_OUTPUT:
        add_property_string(return_value, "type", "output", 1);
        add_property_stringl(return_value, "data", output->data,
            output->length, 1);
        add_property_long(return_value, "stream", output->stream);
        break;
    case REMCTL_OUT_ERROR:
        add_property_string(return_value, "type", "error", 1);
        add_property_stringl(return_value, "data", output->data,
            output->length, 1);
        add_property_long(return_value, "error", output->error);
        break;
    case REMCTL_OUT_STATUS:
        add_property_string(return_value, "type", "status", 1);
        add_property_long(return_value, "status", output->status);
        break;
    case REMCTL_OUT_DONE:
        add_property_string(return_value, "type", "done", 1);
        break;
    }
}


/*
 * Returns the error message from a previously failed remctl call.
 */
ZEND_FUNCTION(remctl_error)
{
    struct remctl *r;
    zval *zrem;
    const char *error;
    int status;

    /* Parse and verify arguments. */
    status = zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "r", &zrem);
    if (status == FAILURE) {
        zend_error(E_WARNING, "remctl_error: invalid parameters\n");
        RETURN_NULL();
    }
    ZEND_FETCH_RESOURCE(r, struct remctl *, &zrem, -1, PHP_REMCTL_RES_NAME,
        le_remctl_internal);

    /* Do the work. */
    error = remctl_error(r);
    RETURN_STRING((char *) error, 1);
}


/*
 * Close the connection.  This isn't strictly necessary since the destructor
 * will close the connection for us, but it's part of the interface.
 */
ZEND_FUNCTION(remctl_close)
{
    struct remctl *r;
    zval *zrem;
    int status;

    /* Parse and verify arguments. */
    status = zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "r", &zrem);
    if (status == FAILURE) {
        zend_error(E_WARNING, "remctl_error: invalid parameters\n");
        RETURN_NULL();
    }
    ZEND_FETCH_RESOURCE(r, struct remctl *, &zrem, -1, PHP_REMCTL_RES_NAME,
        le_remctl_internal);

    /* This delete invokes php_remctl_dtor, which calls remctl_close. */
    zend_list_delete(Z_LVAL_P(zrem));
    RETURN_TRUE;
}
