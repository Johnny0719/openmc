"""
This module provides bindings to C functions defined by OpenMC shared library.
When the :mod:`openmc` package is imported, the OpenMC shared library is
automatically loaded. Calls to the OpenMC library can then be via functions or
objects in the :mod:`openmc.capi` subpackage, for example:

.. code-block:: python

    openmc.capi.init()
    openmc.capi.run()
    openmc.capi.finalize()

"""

from ctypes import CDLL, c_bool
import os
import sys

import pkg_resources


# Determine shared-library suffix
if sys.platform == 'darwin':
    _suffix = 'dylib'
else:
    _suffix = 'so'

if os.environ.get('READTHEDOCS', None) != 'True':
    # Open shared library
    _filename = pkg_resources.resource_filename(
        __name__, 'libopenmc.{}'.format(_suffix))
    _dll = CDLL(_filename)
else:
    # For documentation builds, we don't actually have the shared library
    # available. Instead, we create a mock object so that when the modules
    # within the openmc.capi package try to configure arguments and return
    # values for symbols, no errors occur
    from unittest.mock import Mock
    _dll = Mock()

dagmc_enabled = bool(c_bool.in_dll(_dll, "dagmc_enabled"))
    
from .error import *
from .core import *
from .nuclide import *
from .material import *
from .cell import *
from .mesh import *
from .filter import *
from .tally import *
from .settings import settings
from .math import *
