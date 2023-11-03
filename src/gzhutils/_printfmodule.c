#define PY_SSIZE_T_CLEAN
#include <Python.h>


static PyObject *PrintfError;


static PyObject *
_printf_system(PyObject *self, PyObject *args) {
    const char *command;
    int sts;

    if (!PyArg_ParseTuple(args, "s", &command)) return NULL;
    sts = system(command);
    if (sts < 0) {
        PyErr_SetString(PrintfError, "System command failed");
        return NULL;
    }

    return PyLong_FromLong(sts);
}


static PyObject *
_printf_hello_world(PyObject *self, PyObject *args) {
    printf("Hello, world!\n");

    Py_INCREF(Py_None);
    return Py_None;
}


static PyObject *
_printf_printf(PyObject *self, PyObject *args) {
    const char *string;
    if (!PyArg_ParseTuple(args, "s", &string)) return NULL;
    
    printf(string);

    Py_INCREF(Py_None);
    return Py_None;
}


static PyMethodDef PrintfMethods[] = {
    {"system", _printf_system, METH_VARARGS, "Execute a shell command."},
    {"hello_world", _printf_hello_world, METH_VARARGS, "Prints hello world"},
    {"printf", _printf_printf, METH_VARARGS, "printf without formatted string"},
    {NULL, NULL, 0, NULL}
};


static struct PyModuleDef printfmodule = {
    PyModuleDef_HEAD_INIT,
    "_printf",  // name of module
    NULL,  // module documentation, may be NULL
    -1,
    PrintfMethods
};


PyMODINIT_FUNC
PyInit__printf(void) {
    PyObject *m;

    m = PyModule_Create(&printfmodule);
    if (m == NULL) {
        return NULL;
    }

    PrintfError = PyErr_NewException("_printf.error", NULL, NULL);
    Py_XINCREF(PrintfError);
    if (PyModule_AddObject(m, "error", PrintfError) < 0) {
        Py_XDECREF(PrintfError);
        Py_CLEAR(PrintfError);
        Py_DECREF(m);
    }

    return m;
}