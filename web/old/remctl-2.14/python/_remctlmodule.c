/*
 * Low-level Python interface to remctl.
 *
 * A direct Python equivalent to the libremctl API.  Normally, Python scripts
 * should not use this interface directly; instead, they should use the remctl
 * Python wrapper around this class.
 *
 * Original implementation by Thomas L. Kula <kula@tproa.net>
 * Copyright 2008 Thomas L. Kula <kula@tproa.net>
 * Copyright 2008 Board of Trustees, Leland Stanford Jr. University
 *
 * Permission to use, copy, modify, and distribute this software and its
 * documentation for any purpose and without fee is hereby granted, provided
 * that the above copyright notice appear in all copies and that both that
 * copyright notice and this permission notice appear in supporting
 * documentation, and that the name of Thomas L. Kula not be used in
 * advertising or publicity pertaining to distribution of the software without
 * specific, written prior permission. Thomas L. Kula makes no representations
 * about the suitability of this software for any purpose.  It is provided "as
 * is" without express or implied warranty.
 *
 * THIS SOFTWARE IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
 */

#include <Python.h>

#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <sys/uio.h>
#include <unistd.h>

#include <remctl.h>

/* The type of the argument to PyString_AsStringAndSize changed in 2.5. */
#if PY_VERSION_HEX < 0x02050000 && !defined(PY_SSIZE_T_MIN)
typedef int Py_ssize_t;
# define PY_SSIZE_T_MAX INT_MAX
# define PY_SSIZE_T_MIN INT_MIN
#endif

/* Silence GCC warnings. */
PyMODINIT_FUNC init_remctl(void);

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

static PyObject *
py_remctl(PyObject *self, PyObject *args)
{
    struct remctl_result *rr;
    char *host = NULL;
    unsigned short port;
    char *principal = NULL;
    const char **command = NULL;
    PyObject *list = NULL;
    PyObject *tmp = NULL;
    int length, i;
    PyObject *result = NULL;

    if (!PyArg_ParseTuple(args, "sHzO", &host, &port, &principal, &list))
        return NULL;

    /*
     * The command is passed as a list object.  For the remctl API, we need to
     * turn it into a NULL-terminated array of pointers.
     */
    length = PyList_Size(list);
    command = malloc((length + 1) * sizeof(char *));
    if (command == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    for (i = 0; i < length; i++) {
        tmp = PyList_GetItem(list, i);
        if (tmp == NULL)
            goto end;
        command[i] = PyString_AsString(tmp);
        if (command[i] == NULL)
            goto end;
    }
    command[i] = NULL;

    rr = remctl(host, port, principal, command);
    if (rr == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    result = Py_BuildValue("(ss#s#i)", rr->error,
                           rr->stdout_buf, (int) rr->stdout_len,
                           rr->stderr_buf, (int) rr->stderr_buf,
                           rr->status);
    remctl_result_free(rr);

end:
    if (command != NULL)
        free(command);
    return result;
}


/*
 * Called when the Python object is destroyed.  Clean up the underlying
 * libremctl object.
 */
static void
remctl_destruct(void *r)
{
    remctl_close(r);
}


static PyObject *
py_remctl_new(PyObject *self, PyObject *args)
{
    struct remctl *r;

    r = remctl_new();
    if (r == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    return PyCObject_FromVoidPtr(r, remctl_destruct);
}


static PyObject *
py_remctl_open(PyObject *self, PyObject *args)
{
    PyObject *object = NULL;
    char *host = NULL;
    unsigned short port = 0;
    char *principal = NULL;
    struct remctl *r;
    int status;

    if (!PyArg_ParseTuple(args, "Os|Hz", &object, &host, &port, &principal))
        return NULL;
    r = PyCObject_AsVoidPtr(object);
    status = remctl_open(r, host, port, principal);
    return Py_BuildValue("i", status);
}


static PyObject *
py_remctl_close(PyObject *self, PyObject *args)
{
    PyObject *object = NULL;
    struct remctl *r;

    if (!PyArg_ParseTuple(args, "O", &object))
        return NULL;
    r = PyCObject_AsVoidPtr(object);
    remctl_close(r);
    Py_INCREF(Py_None);
    return Py_None;
}


static PyObject *
py_remctl_error(PyObject *self, PyObject *args)
{
    PyObject *object = NULL;
    struct remctl *r;

    if (!PyArg_ParseTuple(args, "O", &object))
        return NULL;
    r = PyCObject_AsVoidPtr(object);
    return Py_BuildValue("s", remctl_error(r));
}


static PyObject *
py_remctl_commandv(PyObject *self, PyObject *args)
{
    PyObject *object = NULL;
    PyObject *list = NULL;
    struct remctl *r;
    struct iovec *iov;
    size_t count, i;
    char *string;
    Py_ssize_t length;
    PyObject *element;
    PyObject *result = NULL;

    if (!PyArg_ParseTuple(args, "OO", &object, &list))
        return NULL;
    r = PyCObject_AsVoidPtr(object);

    /*
     * Convert the Python list into an array of struct iovecs, each of which
     * pointing to the elements of the list.
     */
    count = PyList_Size(list);
    iov = malloc(count * sizeof(struct iovec));
    if (iov == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    for (i = 0; i < count; i++) {
        element = PyList_GetItem(list, i);
        if (element == NULL)
            goto end;
        if (PyString_AsStringAndSize(element, &string, &length) == -1)
            goto end;
        iov[i].iov_base = string;
        iov[i].iov_len = length;
    }

    if (remctl_commandv(r, iov, count)) {
        Py_INCREF(Py_True);
        result = Py_True;
    } else {
        Py_INCREF(Py_False);
        result = Py_False;
    }

end:
    if (iov != NULL)
        free(iov);
    return result;
}


static PyObject *
py_remctl_output(PyObject *self, PyObject *args)
{
    PyObject *object = NULL;
    struct remctl *r;
    struct remctl_output *output;
    const char *type = "unknown";
    size_t i;
    PyObject *result;

    if (!PyArg_ParseTuple(args, "O", &object))
        return NULL;
    r = PyCObject_AsVoidPtr(object);
    output = remctl_output(r);
    if (output == NULL) {
        Py_INCREF(Py_False);
        return Py_False;
    }
    for (i = 0; OUTPUT_TYPE[i].name != NULL; i++)
        if (OUTPUT_TYPE[i].type == output->type) {
            type = OUTPUT_TYPE[output->type].name;
            break;
        }
    result = Py_BuildValue("ss#iii", type, output->data, output->length,
                           output->stream, output->status, output->error);
    return result;
}


static PyMethodDef methods[] = {
    { "remctl",          py_remctl,          METH_VARARGS, NULL },
    { "remctl_new",      py_remctl_new,      METH_VARARGS, NULL },
    { "remctl_open",     py_remctl_open,     METH_VARARGS, NULL },
    { "remctl_close",    py_remctl_close,    METH_VARARGS, NULL },
    { "remctl_error",    py_remctl_error,    METH_VARARGS, NULL },
    { "remctl_commandv", py_remctl_commandv, METH_VARARGS, NULL },
    { "remctl_output",   py_remctl_output,   METH_VARARGS, NULL },
    { NULL,              NULL,               0,            NULL },
};


PyMODINIT_FUNC
init_remctl(void)
{
    PyObject *module, *dict, *tmp;

    module = Py_InitModule("_remctl", methods);
    dict = PyModule_GetDict(module);

    tmp = PyString_FromString(VERSION);
    PyDict_SetItemString(dict, "VERSION", tmp);
    Py_DECREF(tmp);
}
