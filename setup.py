#!/usr/bin/env python3
import os
import shutil
import platform
from setuptools import setup

if platform.system() in ["Darwin", "Linux"]:
    import pwd

if platform.system() == "Darwin":
    if os.getuid() != 0:
        raise PermissionError("Must be superuser to build for Mac.")

    APP = ["Editor.py"]
    DATA_FILES = []
    OPTIONS = {
        "packages": ["PIL", "pdf2image", "yaml"],
        "resources": [],
        "redirect_stdout_to_asl": True,
    }

    if "arm" in platform.machine():
        OPTIONS["resources"].append("/opt/homebrew/Cellar/poppler/22.02.0/bin")
    elif "x86" in platform.machine():
        OPTIONS["resources"].append("/usr/local/homebrew/Cellar/poppler/22.02.0/bin")
    else:
        raise SystemError(f"Unknown arch: {platform.machine()}")

    setup(
        app=APP,
        data_files=DATA_FILES,
        py_modules=[],
        options={'py2app': OPTIONS},
        setup_requires=['py2app'],
    )

    os.chdir("dist/Editor.app/Contents/Resources/")
    os.symlink("../Frameworks", "Frameworks", target_is_directory=True)
    os.chown("../../", pwd.getpwnam(os.getlogin()).pw_uid, pwd.getpwnam(os.getlogin()).pw_gid)
    if "arm" in platform.machine():
        shutil.copytree("/opt/homebrew/Cellar/poppler/22.02.0/lib/", "../Frameworks", dirs_exist_ok=True)
    else:
        shutil.copytree("/usr/local/homebrew/Cellar/poppler/22.02.0/lib/", "../Frameworks", dirs_exist_ok=True)

    print("Copied libraries over to the app. Test before shipping!")
