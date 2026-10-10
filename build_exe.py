import os
import subprocess
import sys

project_dir = os.path.dirname(os.path.abspath(__file__))
app_name = "karaoke_manager"

cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--onefile",
    "--windowed",
    "--name",
    app_name,
    "karaoke_manager.py",
]

if os.path.exists(os.path.join(project_dir, "icon.ico")):
    cmd.extend(["--icon", "icon.ico"])

print("Building EXE...")
subprocesscess.run(cmd, cwd=project_dir, check=True)
print("Build complete.")
print(f"Executable is in: {os.path.join(project_dir, 'dist')}")
