#-----------------------------------------------------------------------------
# Copyright (c) 2018-2019, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

# hook for https://github.com/r0x0r/pywebview

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = collect_data_files('webview', 'lib')
binaries = collect_dynamic_libs('webview')
