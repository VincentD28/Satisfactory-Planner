# PyInstaller spec: build with  python build_exe.py  (or  pyinstaller SatisfactoryPlanner.spec)
#
# One windowed exe. The pictures and the cleaned game data ride inside it, where
# data_maker.data_file() falls back to them (img/<name> and <name> under
# sys._MEIPASS), so the exe runs on its own - even on a machine whose
# AppData\Roaming\Satisfactory-Planner (data_maker.DATA) has no data yet.
import glob
import os
import sys

ROOT = os.path.abspath(SPECPATH)
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import data_maker

datas = [(path, "img") for path in glob.glob(os.path.join(ROOT, "Images", "*"))]
datas.append((os.path.join(data_maker.DATA, "cleaned_data.json"), "."))

icon = os.path.join(ROOT, "build", "icon.ico")

a = Analysis(
    [os.path.join(ROOT, "Scripts", "Interface.py")],
    pathex=[os.path.join(ROOT, "Scripts")],
    datas=datas,
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
              "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia"],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="SatisfactoryPlanner",
    console=False,
    icon=icon if os.path.exists(icon) else None,
    upx=False,
)
