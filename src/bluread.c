#include "bluread.h"

// --------------------------------------------------------------------------------
// --------------------------------------------------------------------------------
// PyObject types structs

typedef struct {
	PyObject_HEAD
	PyObject *path;

	BLURAY *BR;
} Bluray;

// Predefine them so they can be used below since their full definition references the functions below
static PyTypeObject BlurayType;

// --------------------------------------------------------------------------------
// --------------------------------------------------------------------------------
// Administrative functions for Bluray

static PyObject* Bluray_Close(Bluray *self);

static PyObject*
Bluray_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	Bluray *self;

	self = (Bluray*)type->tp_alloc(type, 0);
	if (self)
	{
		Py_INCREF(Py_None);
		self->path = Py_None;

		self->BR = NULL;
	}

	return (PyObject*)self;
}

static int
Bluray_init(Bluray *self, PyObject *args, PyObject *kwds)
{
	PyObject *path=NULL, *tmp=NULL;
	static char *kwlist[] = {"Path", NULL};

	if (! PyArg_ParseTupleAndKeywords(args,kwds, "O", kwlist, &path))
	{
		return -1;
	}

	// Allocated in Bluray_Open
	self->BR = NULL;

	// Path
	tmp = self->path;
	self->path = path;
	Py_INCREF(path);
	Py_CLEAR(tmp);

	return 0;
}

static void
Bluray_dealloc(Bluray *self)
{
	Py_CLEAR(self->path);

	if (self->BR)
	{
		Bluray_Close(self);
	}
	self->BR = NULL;

	Py_TYPE(self)->tp_free((PyObject*)self);
}

// --------------------------------------------------------------------------------
// --------------------------------------------------------------------------------
// Interface stuff for Bluray

static PyObject*
Bluray_getPath(Bluray *self)
{
	if (self->path == NULL)
	{
		PyErr_SetString(PyExc_AttributeError, "_path");
		return NULL;
	}

	Py_INCREF(self->path);
	return self->path;
}

static int
_Bluray_getIsOpen(Bluray *self)
{
	return !!self->BR;
}

static PyObject*
Bluray_getIsOpen(Bluray *self)
{
	if ( _Bluray_getIsOpen(self) )
	{
		Py_INCREF(Py_True);
		return Py_True;
	}
	else
	{
		Py_INCREF(Py_False);
		return Py_False;
	}
}

static PyObject*
Bluray_Open(Bluray *self)
{
	if (_Bluray_getIsOpen(self))
	{
		PyErr_SetString(PyExc_Exception, "Device is already open, first Close() it to re-open");
		return NULL;
	}

	char *charpath = PyUnicode_AsUTF8(self->path);
	if (charpath == NULL)
	{
		return NULL;
	}

	char *keyfile_charpath = NULL;

	if (! bd_open_disc(self->BR, charpath, keyfile_charpath))
	{
		PyErr_SetString(PyExc_Exception, "Failed to open device");
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject*
Bluray_Close(Bluray *self)
{
	if (! _Bluray_getIsOpen(self))
	{
		PyErr_SetString(PyExc_Exception, "Device not open, cannot close it");
		return NULL;
	}

	if (self->BR)
	{
		// bd_close() calls free() on the BLURAY object itself, so nothing to match bd_init()
		bd_close(self->BR);
	}
	self->BR = NULL;

	Py_INCREF(Py_None);
	return Py_None;
}


static PyMemberDef Bluray_members[] = {
	{"_path", T_OBJECT_EX, offsetof(Bluray, path), 0, "Path of Bluray device"},
	{NULL}
};

static PyMethodDef Bluray_methods[] = {
	{"Open", (PyCFunction)Bluray_Open, METH_NOARGS, "Opens the device for reading"},
	{"Close", (PyCFunction)Bluray_Close, METH_NOARGS, "Closes the device"},
	{NULL}
};

static PyGetSetDef Bluray_getseters[] = {
	{"IsOpen", (getter)Bluray_getIsOpen, NULL, "Gets flag indicating if device is open or not", NULL},
	{"Path", (getter)Bluray_getPath, NULL, "Get the path to the Bluray device", NULL},
	{NULL}
};


// --------------------------------------------------------------------------------
// --------------------------------------------------------------------------------
// Fully define PyObject types now

static PyTypeObject BlurayType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"_bluread.Bluray",         /* tp_name */
	sizeof(Bluray),            /* tp_basicsize */
	0,                         /* tp_itemsize */
	(destructor)Bluray_dealloc,/* tp_dealloc */
	0,                         /* tp_print */
	0,                         /* tp_getattr */
	0,                         /* tp_setattr */
	0,                         /* tp_reserved */
	0,                         /* tp_repr */
	0,                         /* tp_as_number */
	0,                         /* tp_as_sequence */
	0,                         /* tp_as_mapping */
	0,                         /* tp_hash  */
	0,                         /* tp_call */
	0,                         /* tp_str */
	0,                         /* tp_getattro */
	0,                         /* tp_setattro */
	0,                         /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,        /* tp_flags */
	"Represents a BLURAY from libbluray",          /* tp_doc */
	0,                         /* tp_traverse */
	0,                         /* tp_clear */
	0,                         /* tp_richcompare */
	0,                         /* tp_weaklistoffset */
	0,                         /* tp_iter */
	0,                         /* tp_iternext */
	Bluray_methods,            /* tp_methods */
	Bluray_members,            /* tp_members */
	Bluray_getseters,          /* tp_getset */
	0,                         /* tp_base */
	0,                         /* tp_dict */
	0,                         /* tp_descr_get */
	0,                         /* tp_descr_set */
	0,                         /* tp_dictoffset */
	(initproc)Bluray_init,     /* tp_init */
	0,                         /* tp_alloc */
	Bluray_new,                /* tp_new */
};

// --------------------------------------------------------------------------------
// --------------------------------------------------------------------------------
// Define the module

static PyMethodDef BluReadModuleMethods[] = {
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef BluReadmodule = {
	PyModuleDef_HEAD_INIT,
	"_bluread",
	"Python wrapper for libbluray", // Doc
	-1, // state in global vars
	BluReadModuleMethods
};

PyMODINIT_FUNC
PyInit__bluread(void)
{
	PyObject *m = PyModule_Create(&BluReadModule);
	if (m == NULL)
	{
		return NULL;
	}

	return m;
}

