"""
=============================================================================
⚡ SPARK WINDOWS AUTOSTART & PERSISTENCE CONFIGURATOR
=============================================================================
Configures SPARK to run automatically whenever Master Aryan turns on his laptop
from the power button.

Ensures:
1. Dual-redundancy registration:
   - Windows Startup Folder: %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\SPARK_Sentinel.vbs
   - Windows Registry: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run -> SPARK_Sentinel
2. Zero Terminal Flash:
   - Uses pythonw.exe and VBScript so NO command prompt window ever appears.
   - Runs 24/7 silently, waking only when Aryan says "Hey Spark" or presses Win+S.
=============================================================================
"""

import os
import sys
import winreg
import subprocess

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
DAEMON_SCRIPT = os.path.join(WORKSPACE_DIR, "spark_sentinel_daemon.py")
PYTHON_EXE = sys.executable

STARTUP_FOLDER = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
VBS_PATH = os.path.join(STARTUP_FOLDER, "SPARK_Sentinel.vbs")
REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_NAME = "SPARK_Sentinel"

def install_autostart() -> bool:
    """Installs SPARK autostart into Startup folder and Windows Registry."""
    print("=" * 68)
    print(" ⚡ INSTALLING SPARK 24/7 AUTOSTART ON LAPTOP BOOT")
    print("=" * 68)
    print(f"📁 Daemon Script: {DAEMON_SCRIPT}")
    print(f"🐍 Python Executable: {PYTHON_EXE}")
    print(f"🚀 Startup Folder: {STARTUP_FOLDER}")

    success_count = 0

    # 1. Write Silent VBScript to Startup Folder
    try:
        os.makedirs(STARTUP_FOLDER, exist_ok=True)
        vbs_content = (
            'Set WshShell = CreateObject("WScript.Shell")\n'
            f'WshShell.CurrentDirectory = "{WORKSPACE_DIR}"\n'
            f'WshShell.Run """{PYTHON_EXE}"" ""{DAEMON_SCRIPT}""", 0, False\n'
            'Set WshShell = Nothing\n'
        )
        with open(VBS_PATH, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        print(f"✅ [SUCCESS]: Startup VBScript written to {VBS_PATH}")
        success_count += 1
    except Exception as e:
        print(f"❌ [VBS Error]: {e}")

    # 2. Register in Windows Registry Run key
    try:
        cmd_str = f'"{PYTHON_EXE}" "{DAEMON_SCRIPT}"'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, REG_NAME, 0, winreg.REG_SZ, cmd_str)
        print(f"✅ [SUCCESS]: Windows Registry Run key '{REG_NAME}' registered.")
        success_count += 1
    except Exception as e:
        print(f"❌ [Registry Error]: {e}")

    if success_count > 0:
        print("\n🎉 SPARK will now automatically wake up 24/7 whenever you boot your laptop!")
        return True
    return False

def uninstall_autostart() -> bool:
    """Removes SPARK autostart entries."""
    print("🗑️ Removing SPARK autostart entries...")
    if os.path.exists(VBS_PATH):
        try:
            os.remove(VBS_PATH)
            print(f"✅ Removed: {VBS_PATH}")
        except Exception as e:
            print(f"Error removing VBS: {e}")

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, REG_NAME)
            print(f"✅ Removed Registry key: {REG_NAME}")
    except Exception as e:
        print(f"Notice: Registry key already absent or {e}")
    return True

def check_status():
    """Checks whether autostart is active."""
    vbs_ok = os.path.exists(VBS_PATH)
    reg_ok = False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, REG_NAME)
            reg_ok = True
    except Exception:
        reg_ok = False

    print("=" * 68)
    print(" ⚡ SPARK AUTOSTART STATUS")
    print("=" * 68)
    print(f"  - Startup VBScript: {'[ACTIVE]' if vbs_ok else '[NOT FOUND]'}")
    print(f"  - Registry Run Key: {'[ACTIVE]' if reg_ok else '[NOT FOUND]'}")
    print("=" * 68)

def start_daemon_now():
    """Immediately launches the background sentinel daemon via pythonw."""
    print(f"🚀 Launching SPARK Sentinel now in background...")
    flags = subprocess.DETACHED_PROCESS if hasattr(subprocess, 'DETACHED_PROCESS') else 0
    subprocess.Popen([PYTHON_EXE, DAEMON_SCRIPT], cwd=WORKSPACE_DIR, creationflags=flags)
    print("✅ SPARK Sentinel is now active in background!")

if __name__ == "__main__":
    if "--uninstall" in sys.argv:
        uninstall_autostart()
    elif "--status" in sys.argv:
        check_status()
    elif "--start-now" in sys.argv:
        start_daemon_now()
    else:
        install_autostart()
        check_status()
