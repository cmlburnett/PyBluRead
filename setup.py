import sys
from setuptools import setup, Extension

majv = 1
minv = 5

if sys.version_info < (3,):
    print("This library is only tested with Python 3.7")
    sys.exit(1)

bluray = Extension(
    '_bluread',
    define_macros=[
        ('MAJOR_VERSION', str(majv)),
        ('MINOR_VERSION', str(minv))
    ],
	include_dirs = ['/usr/include/libbluray'],
    libraries=['bluray'],
    sources=['src/bluread.c']
)

setup(
    name='bluread',
    version='%d.%d' % (majv, minv),
    description='Python wrapper for libbluray',
    author='Colin ML Burnett',
    author_email='cmlburnett@gmail.com',
    url="https://github.com/3ll3d00d/PyBluRead",
    download_url="https://pypi.python.org/pypi/bluread",
    packages=['bluread'],
    ext_modules=[bluray],
    requires=['crudexml'],
    classifiers=[
        'Programming Language :: Python :: 3.7'
    ]
)
