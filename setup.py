#!/usr/bin/env python

import glob
import sys
import os
import distutils.core
import distutils.sysconfig

package="thanlwinsoft.translate"
pkg_dir = "thanlwinsoft" + os.sep + "translate"

if (sys.platform.find("linux") > -1):
    if "--install-layout" in sys.argv :
        packagesdir = distutils.sysconfig.get_python_lib()
    else :
        packagesdir = distutils.sysconfig.get_python_lib(prefix="/usr/local")
else :
    packagesdir = distutils.sysconfig.get_python_lib()

data_files = glob.glob(pkg_dir + os.sep +  "*.png") + glob.glob(pkg_dir + os.sep + "*.glade")
options = {}

distutils.core.setup(
    name="podiff",
    version="0.1.0",
    description="Utility to compare translation files",
    long_description="Supports comparing 2 translation files or merging of translation files from 2 branches",
    author="Keith Stribley",
    author_email="devel@thanlwinsoft.org",
    url="http://www.thanlwinsoft.org/",
    packages = [package],
    platforms=["any"],
    license="GNU General Public License (GPL)",
    scripts = [pkg_dir + os.sep + "podiffgtk"],
    data_files = [[packagesdir + os.sep + pkg_dir, data_files]],
    options = options
)

