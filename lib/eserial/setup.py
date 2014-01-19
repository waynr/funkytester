
try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command

import sys

setup(
    name = "EnhancedSerial",
    url = 'http://git.emacinc.com/public/eserial.py',
    author = 'Wayne Warren',
    author_email = 'waynr@paunix.org',
    maintainer = 'Wayne Warren',
    maintainer_email = 'waynr@paunix.org',
    description = 'Enhanced Python Serial Interace',
    license = "Python",
    py_modules = ["eserial"],
    install_requires = [
        "pyserial >= 2.5"
        ]
)
