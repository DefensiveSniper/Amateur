# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

project_dir = os.path.abspath(os.getcwd())

datas = []
def add_dir(rel):
    src = os.path.join(project_dir, rel)
    if os.path.exists(src):
        datas.append((src, rel))

for rel in ["templates", "static", "func", "base", "libs", "cache", "tools", "requirements.txt", "config.json"]:
    add_dir(rel)

# 有些库（比如 Azure 语音）需要打包动态库
binaries = collect_dynamic_libs("azure.cognitiveservices.speech")

a = Analysis(
    ['flask_server.py'],
    pathex=[project_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'engineio.async_drivers.threading',
        'socketio.async_drivers.threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 注意：这里做一个“带窗口”的 EXE（不显示控制台）
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='flask_server-x86_64-pc-windows-msvc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # ✅ 不要控制台
    disable_windowed_traceback=False,
    target_arch=None,
)

# 关键：使用 COLLECT → onedir 布局（不是 onefile）
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='flask_server',     # dist/flask_server/ 目录
)
