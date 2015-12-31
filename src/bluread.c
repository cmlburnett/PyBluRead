#include "bluread.h"

// --------------------------------------------------------------------------------
// --------------------------------------------------------------------------------
// PyObject types structs

typedef struct {
	PyObject_HEAD
	PyObject *path;
	PyObject *keydb;

	BLURAY *BR;
	const BLURAY_DISC_INFO *info;

	PyObject* TitleClass;

	int numtitles;
} Bluray;

typedef struct {
	PyObject_HEAD
	int titlenum;

	Bluray *br;

	BLURAY_TITLE_INFO *info;

} Title;

// Predefine them so they can be used below since their full definition references the functions below
static PyTypeObject BlurayType;
static PyTypeObject TitleType;

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

		Py_INCREF(Py_None);
		self->keydb = Py_None;

		self->BR = NULL;
		self->info = NULL;
		self->TitleClass = NULL;

		self->numtitles = 0;
	}

	return (PyObject*)self;
}

static int
Bluray_init(Bluray *self, PyObject *args, PyObject *kwds)
{
	PyObject *path=NULL, *keydb=NULL, *titleclass=NULL, *tmp=NULL;
	static char *kwlist[] = {"Path", "KeyDB", "TitleClass", NULL};

	if (! PyArg_ParseTupleAndKeywords(args,kwds, "OOO", kwlist, &path, &keydb, &titleclass))
	{
		return -1;
	}

	// Allocated in Bluray_Open
	self->BR = NULL;
	self->info = NULL;

	// Path
	tmp = self->path;
	self->path = path;
	Py_INCREF(path);
	Py_CLEAR(tmp);

	// Path
	tmp = self->keydb;
	self->keydb = keydb;
	Py_INCREF(keydb);
	Py_CLEAR(tmp);

	// TitleClass
	tmp = self->TitleClass;
	self->TitleClass = titleclass;
	Py_INCREF(titleclass);
	Py_CLEAR(tmp);

	return 0;
}

static void
Bluray_dealloc(Bluray *self)
{
	Py_CLEAR(self->path);
	Py_CLEAR(self->keydb);

	if (self->BR)
	{
		Bluray_Close(self);
	}
	self->BR = NULL;
	self->info = NULL; // an inner structure of BLURAY, nothing to free

	Py_TYPE(self)->tp_free((PyObject*)self);
}

// --------------------------------------------------------------------------------
// --------------------------------------------------------------------------------
// Interface stuff for Bluray

static int
_Bluray_getIsOpen(Bluray *self)
{
	return !!self->BR;
}

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

static PyObject*
Bluray_getKeyDB(Bluray *self)
{
	if (self->keydb == NULL)
	{
		PyErr_SetString(PyExc_AttributeError, "_keydb");
		return NULL;
	}

	Py_INCREF(self->keydb);
	return self->keydb;
}

static PyObject*
Bluray_getNumberOfTitles(Bluray *self)
{
	if (! _Bluray_getIsOpen(self))
	{
		PyErr_SetString(PyExc_Exception, "Device not open, must Open() it first before accessing it");
		return NULL;
	}

	return PyLong_FromLong((long)self->numtitles);
}

static PyObject*
Bluray_getMainTitleNumber(Bluray *self)
{
	if (! _Bluray_getIsOpen(self))
	{
		PyErr_SetString(PyExc_Exception, "Device not open, must Open() it first before accessing it");
		return NULL;
	}

	int num = bd_get_main_title(self->BR);
	if (num < 0)
	{
		PyErr_SetString(PyExc_Exception, "Unable to get main title number");
		return NULL;
	}

	return PyLong_FromLong((long)num);
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

	// Allocate space for BLURAY structure
	self->BR = bd_init();

	if (! bd_open_disc(self->BR, charpath, keyfile_charpath))
	{
		PyErr_SetString(PyExc_Exception, "Failed to open device");
		goto error;
	}

	// Get basic disc information
	self->info = bd_get_disc_info(self->BR);
	if (self->info == NULL)
	{
		PyErr_SetString(PyExc_Exception, "Failed to get disc info");
		goto error;
	}

	// No flags (0) and no minimum title time (0)
	self->numtitles = bd_get_titles(self->BR, 0, 0);
	if (self->numtitles <= 0)
	{
		PyErr_SetString(PyExc_Exception, "Failed to get titles");
		goto error;
	}

	Py_INCREF(Py_None);
	return Py_None;

error:
	if (self->BR)
	{
		bd_close(self->BR);
	}
	self->BR = NULL;
	self->info = NULL;

	self->numtitles = 0;

	return NULL;
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
	self->info = NULL;

	self->numtitles = 0;

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject*
Bluray_GetTitle(Bluray *self, PyObject *args)
{
	if (! _Bluray_getIsOpen(self))
	{
		PyErr_SetString(PyExc_Exception, "Device not open, must Open() it first before accessing it");
		return NULL;
	}

	int num=0;

	if (! PyArg_ParseTuple(args, "i", &num))
	{
		return NULL;
	}

	if (num < 0)
	{
		PyErr_Format(PyExc_Exception, "Title number (%d) must be non-negative", num);
		return NULL;
	}
	if (num > self->numtitles)
	{
		PyErr_Format(PyExc_Exception, "Title number (%d) must be non-negative but it exceeds the number (%d) of available titles", num,self->numtitles);
		return NULL;
	}

	PyObject *a = Py_BuildValue("Oi", self, num);
	if (a == NULL)
	{
		return NULL;
	}

	return PyObject_CallObject(self->TitleClass, a);
}


static PyMemberDef Bluray_members[] = {
	{"_path", T_OBJECT_EX, offsetof(Bluray, path), 0, "Path of Bluray device"},
	{"_keydb", T_OBJECT_EX, offsetof(Bluray, keydb), 0, "KEYDB.cfg location"},
	{NULL}
};

static PyMethodDef Bluray_methods[] = {
	{"Open", (PyCFunction)Bluray_Open, METH_NOARGS, "Opens the device for reading"},
	{"Close", (PyCFunction)Bluray_Close, METH_NOARGS, "Closes the device"},
	{"GetTitle", (PyCFunction)Bluray_GetTitle, METH_VARARGS, "Gets title information"},
	{NULL}
};

static PyGetSetDef Bluray_getseters[] = {
	{"IsOpen", (getter)Bluray_getIsOpen, NULL, "Gets flag indicating if device is open or not", NULL},
	{"Path", (getter)Bluray_getPath, NULL, "Get the path to the Bluray device", NULL},
	{"KeyDB", (getter)Bluray_getKeyDB, NULL, "Get the path to the KEYDB.cfg file", NULL},
	{"MainTitleNumber", (getter)Bluray_getMainTitleNumber, NULL, "Gets the main title number of the disc", NULL},
	{"NumberOfTitles", (getter)Bluray_getNumberOfTitles, NULL, "Gets the number of titles on this disc", NULL},
	{NULL}
};

// --------------------------------------------------------------------------------
// --------------------------------------------------------------------------------
// Administrative functions for Title

static PyObject*
Title_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	Title *self;

	self = (Title*)type->tp_alloc(type, 0);
	if (self)
	{
		self->br = NULL;
		self->info = NULL;
		self->titlenum = 0;
	}

	return (PyObject*)self;
}

static int
Title_init(Title *self, PyObject *args, PyObject *kwds)
{
	PyObject *br=NULL, *tmp=NULL;
	int num=0;
	static char *kwlist[] = {"br", "num", NULL};

	if (! PyArg_ParseTupleAndKeywords(args,kwds, "Oi", kwlist, &br, &num))
	{
		return -1;
	}

	// br
	tmp = (PyObject*)self->br;
	self->br = (Bluray*)br;
	Py_INCREF(br);
	Py_CLEAR(tmp);

	self->titlenum = num;

	// Get title information for angle 0
	self->info = bd_get_title_info(self->br->BR, self->titlenum, 0);
	if (self->info == NULL)
	{
		Py_XDECREF(br);
		PyErr_SetString(PyExc_Exception, "Failed to get title information from disc");
		return -1;
	}

	return 0;
}

static void
Title_dealloc(Title *self)
{
	if (self->info)
	{
		bd_free_title_info(self->info);
	}
	self->info = NULL;

	self->titlenum = 0;
	Py_CLEAR(self->br);

	Py_TYPE(self)->tp_free((PyObject*)self);
}

// --------------------------------------------------------------------------------
// --------------------------------------------------------------------------------
// Interface stuff for Title

static PyObject*
Title_getNum(Title *self)
{
	if (! _Bluray_getIsOpen(self->br))
	{
		PyErr_SetString(PyExc_Exception, "Device not open, must Open() it first before accessing it");
		return NULL;
	}

	return PyLong_FromLong((long)self->titlenum);
}

static PyObject*
Title_getLength(Title *self)
{
	if (! _Bluray_getIsOpen(self->br))
	{
		PyErr_SetString(PyExc_Exception, "Device not open, must Open() it first before accessing it");
		return NULL;
	}

	return PyLong_FromLong((long)self->info->duration);
}

static PyObject*
Title_getNumberOfAngles(Title *self)
{
	if (! _Bluray_getIsOpen(self->br))
	{
		PyErr_SetString(PyExc_Exception, "Device not open, must Open() it first before accessing it");
		return NULL;
	}

	return PyLong_FromLong((long)self->info->angle_count);
}

static PyObject*
Title_getNumberOfChapters(Title *self)
{
	if (! _Bluray_getIsOpen(self->br))
	{
		PyErr_SetString(PyExc_Exception, "Device not open, must Open() it first before accessing it");
		return NULL;
	}

	return PyLong_FromLong((long)self->info->chapter_count);
}

static PyObject*
Title_getNumberOfClips(Title *self)
{
	if (! _Bluray_getIsOpen(self->br))
	{
		PyErr_SetString(PyExc_Exception, "Device not open, must Open() it first before accessing it");
		return NULL;
	}

	return PyLong_FromLong((long)self->info->clip_count);
}


static PyMemberDef Title_members[] = {
	{"_num", T_OBJECT_EX, offsetof(Title, titlenum), 0, "Title number"},
	{NULL}
};

static PyMethodDef Title_methods[] = {
	//{"Open", (PyCFunction)Title_Open, METH_NOARGS, "Opens the device for reading"},
	{NULL}
};

static PyGetSetDef Title_getseters[] = {
	{"Num", (getter)Title_getNum, NULL, "Get the title number of this title", NULL},
	{"Length", (getter)Title_getLength, NULL, "Get the duration of this title", NULL},
	{"NumberOfAngles", (getter)Title_getNumberOfAngles, NULL, "Gets the number of angles in this title", NULL},
	{"NumberOfChapters", (getter)Title_getNumberOfChapters, NULL, "Gets the number of chapters in this title", NULL},
	{"NumberOfClips", (getter)Title_getNumberOfClips, NULL, "Gets the number of clips in this title", NULL},
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

static PyTypeObject TitleType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"_bluread.Title",          /* tp_name */
	sizeof(Title),             /* tp_basicsize */
	0,                         /* tp_itemsize */
	(destructor)Title_dealloc, /* tp_dealloc */
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
	Title_methods,             /* tp_methods */
	Title_members,             /* tp_members */
	Title_getseters,           /* tp_getset */
	0,                         /* tp_base */
	0,                         /* tp_dict */
	0,                         /* tp_descr_get */
	0,                         /* tp_descr_set */
	0,                         /* tp_dictoffset */
	(initproc)Title_init,      /* tp_init */
	0,                         /* tp_alloc */
	Title_new,                 /* tp_new */
};

// --------------------------------------------------------------------------------
// --------------------------------------------------------------------------------
// Define the module

static PyMethodDef BluReadModuleMethods[] = {
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef BluReadModule = {
	PyModuleDef_HEAD_INIT,
	"_bluread",
	"Python wrapper for libbluray", // Doc
	-1, // state in global vars
	BluReadModuleMethods
};

PyMODINIT_FUNC
PyInit__bluread(void)
{
	// Ready the types
	if(PyType_Ready(&BlurayType) < 0) { return NULL; }
	if(PyType_Ready(&TitleType) < 0) { return NULL; }

	// Create the module defined in the struct above
	PyObject *m = PyModule_Create(&BluReadModule);
	if (m == NULL)
	{
		return NULL;
	}

	// Not sure of a better way to do this, but form a string containing the version
	char v[32];
	sprintf(v, "%d.%d", MAJOR_VERSION, MINOR_VERSION);

	// Add the types to the module
	Py_INCREF(&BlurayType);
	PyModule_AddObject(m, "Bluray", (PyObject*)&BlurayType);
	PyModule_AddObject(m, "Title", (PyObject*)&TitleType);
	PyModule_AddStringConstant(m, "Version", v);

	return m;
}

