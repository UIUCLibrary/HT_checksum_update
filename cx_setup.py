import os
import sys
import cx_Freeze
import pytest
import hathi_checksum
import platform
import re


def create_msi_tablename(python_name, fullname):
    shortname = python_name[:6].replace("_", "").upper()
    longname = fullname
    return "{}|{}".format(shortname, longname)


PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
MSVC = os.path.join(PYTHON_INSTALL_DIR, 'vcruntime140.dll')


def get_tests():
    root = "tests"
    test_files = []
    for x in filter(lambda x: x.is_file and os.path.splitext(x.name)[1] == ".py", os.scandir(root)):
        test_files.append(os.path.join(root, x.name))
    print("Found files {}".format(", ".join(test_files)))
    return test_files


INCLUDE_FILES = [
    "documentation.url",
] + get_tests()

directory_table = [
    (
        "ProgramMenuFolder",  # Directory
        "TARGETDIR",  # Directory_parent
        "PMenu|Programs",  # DefaultDir
    ),
    (
        "PMenu",  # Directory
        "ProgramMenuFolder",  # Directory_parent
        create_msi_tablename(hathi_checksum.__title__, hathi_checksum.FULL_TITLE)
    ),
]
shortcut_table = [
    (
        "startmenuShortcutDoc",  # Shortcut
        "PMenu",  # Directory_
        "{} Documentation".format(create_msi_tablename(hathi_checksum.__title__, hathi_checksum.FULL_TITLE)),
        "TARGETDIR",  # Component_
        "[TARGETDIR]documentation.url",  # Target
        None,  # Arguments
        None,  # Description
        None,  # Hotkey
        None,  # Icon
        None,  # IconIndex
        None,  # ShowCmd
        'TARGETDIR'  # WkDir
    ),
]

if os.path.exists(MSVC):
    INCLUDE_FILES.append(MSVC)

build_exe_options = {
    "includes":
        pytest.freeze_includes(),
    "include_msvcr": True,
    "packages": [
        "os",
        'pytest',
        # "lxml",
        "packaging",
        "six",
        "appdirs",
        # "tests",
        "hathi_checksum"
    ],
    "excludes": ["tkinter"],
    # "namespace_packages": ["tests"],
    "include_files": INCLUDE_FILES,

}
version_extractor = re.compile("\d+[.]\d+[.]\d+")
version = version_extractor.search(hathi_checksum.__version__).group(0)


target_name = "udhtchecksum.exe" if platform.system() == "Windows" else "udhtchecksum"
cx_Freeze.setup(
    name=hathi_checksum.FULL_TITLE,
    description=hathi_checksum.__description__,
    license="University of Illinois/NCSA Open Source License",
    version=version,
    author=hathi_checksum.__author__,
    author_email=hathi_checksum.__author_email__,
    options={
        "build_exe": build_exe_options,
        "bdist_msi": {
            "upgrade_code": "{F212C57B-E55D-40F7-88DC-A49CB97EFA50}",
            "data": {
                "Shortcut": shortcut_table,
                "Directory": directory_table
            },

        }
    },
    executables=[cx_Freeze.Executable("hathi_checksum/__main__.py",
                            targetName=target_name, base="Console")],

)
