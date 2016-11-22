# -----------------------------------------------------------------------------
# Copyright (c) 2005-2016, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

"""
warning for 'import queue' in 2.7 from the future

Problem appears to be that pyinstaller cannot have two modules of the same
name that differ only by lower/upper case.  The from the future 'queue' simply
imports all of the 'Queue' module.  So by my reading, since 'queue' and 'Queue'
can not coexist in a frozen app, and since 'queue' requires 'Queue', there is
no way to use 'queue' in a frozen 2.7 app.
"""

from PyInstaller.compat import is_py2
from PyInstaller.utils.hooks import logger


def pre_find_module_path(api):
    if not is_py2:
        return

    # maybe the 'import queue' was not really needed, so just make sure it
    # is not found, otherwise it will crowd out the potential future
    # import of 'Queue'
    api.search_dirs = []
    logger.warning("import queue (lowercase), not supported")
