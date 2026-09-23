# Builds dist/SatisfactoryPlanner.exe:  python build_exe.py
#
# Makes the exe's icon from Images/Gear_Logo.png (with Qt, so no Pillow needed),
# runs PyInstaller on SatisfactoryPlanner.spec, then copies Data/ beside the exe
# so the projects saved from the scripts open in the exe too.
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist")


def make_icon():
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication, QImage

    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    logo = QImage(os.path.join(ROOT, "Images", "Gear_Logo.png"))
    if logo.isNull():
        return
    os.makedirs(BUILD, exist_ok=True)
    logo = logo.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    logo.save(os.path.join(BUILD, "icon.ico"), "ICO")
    del app


def main():
    make_icon()
    subprocess.check_call([sys.executable, "-m", "PyInstaller", "--noconfirm",
                           "--distpath", DIST, "--workpath", os.path.join(BUILD, "pyinstaller"),
                           os.path.join(ROOT, "SatisfactoryPlanner.spec")])
    shutil.copytree(os.path.join(ROOT, "Data"), os.path.join(DIST, "Data"), dirs_exist_ok=True)
    print("\nbuilt", os.path.join(DIST, "SatisfactoryPlanner.exe"))


if __name__ == "__main__":
    main()
