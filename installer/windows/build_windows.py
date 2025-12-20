"""
GridBot Chuck - Windows Build Script

This script creates a complete Windows installer package including:
1. Python bot bundled with PyInstaller
2. Electron desktop app
3. NSIS installer that packages everything together
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.parent.parent
INSTALLER_DIR = ROOT_DIR / "installer" / "windows"
DESKTOP_DIR = ROOT_DIR / "desktop"
BUILD_DIR = ROOT_DIR / "build"
DIST_DIR = ROOT_DIR / "dist"

def print_step(message):
    """Print a formatted step message."""
    print(f"\n{'=' * 60}")
    print(f"  {message}")
    print(f"{'=' * 60}\n")

def run_command(cmd, cwd=None):
    """Run a command and check for errors."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout

def clean_build_dirs():
    """Clean previous build artifacts."""
    print_step("Cleaning previous builds")

    dirs_to_clean = [BUILD_DIR, DIST_DIR]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"Removing {dir_path}")
            shutil.rmtree(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)

def bundle_python_bot():
    """Bundle Python bot with PyInstaller."""
    print_step("Bundling Python bot with PyInstaller")

    # Create PyInstaller spec if it doesn't exist
    spec_file = INSTALLER_DIR / "gridbot.spec"
    if not spec_file.exists():
        create_pyinstaller_spec()

    # Run PyInstaller
    run_command([
        sys.executable, "-m", "PyInstaller",
        str(spec_file),
        "--clean",
        "--noconfirm"
    ], cwd=ROOT_DIR)

    print("✅ Python bot bundled successfully")

def create_pyinstaller_spec():
    """Create PyInstaller spec file."""
    print("Creating PyInstaller spec file...")

    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../../main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../../config', 'config'),
        ('../../strategies', 'strategies'),
        ('../../web', 'web'),
        ('../../setup_wizard', 'setup_wizard'),
    ],
    hiddenimports=[
        'ccxt',
        'aiosqlite',
        'apprise',
        'pandas',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GridBotChuck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../../desktop/assets/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GridBotChuck',
)
"""

    spec_file = INSTALLER_DIR / "gridbot.spec"
    spec_file.write_text(spec_content)
    print(f"Created spec file: {spec_file}")

def build_electron_app():
    """Build Electron desktop app."""
    print_step("Building Electron desktop app")

    # Install npm dependencies
    print("Installing npm dependencies...")
    run_command(["npm", "install"], cwd=DESKTOP_DIR)

    # Build Electron app
    print("Building Electron app...")
    run_command(["npm", "run", "build:win"], cwd=DESKTOP_DIR)

    print("✅ Electron app built successfully")

def create_nsis_installer():
    """Create NSIS installer script."""
    print_step("Creating NSIS installer")

    nsis_script = INSTALLER_DIR / "installer.nsi"
    if not nsis_script.exists():
        create_nsis_script()

    # Run NSIS compiler
    nsis_path = find_nsis()
    if not nsis_path:
        print("❌ NSIS not found. Please install NSIS from https://nsis.sourceforge.io/")
        print("Skipping installer creation...")
        return

    print(f"Running NSIS from: {nsis_path}")
    run_command([nsis_path, str(nsis_script)])

    print("✅ Installer created successfully")

def find_nsis():
    """Find NSIS compiler."""
    common_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    # Try to find in PATH
    result = shutil.which("makensis")
    return result

def create_nsis_script():
    """Create NSIS installer script."""
    print("Creating NSIS script...")

    nsis_content = r"""
; GridBot Chuck Installer Script

!define PRODUCT_NAME "GridBot Chuck"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "GridBot Chuck"
!define PRODUCT_WEB_SITE "https://github.com/your-repo/gridbotchuck"

!include "MUI2.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "..\..\desktop\assets\icon.ico"
!define MUI_UNICON "..\..\desktop\assets\icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"

; Installer settings
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\..\dist\GridBotChuck-Setup-${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES64\GridBot Chuck"
ShowInstDetails show
ShowUnInstDetails show

; Main installer section
Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    SetOverwrite on

    ; Copy Electron app
    File /r "..\..\desktop\dist\win-unpacked\*.*"

    ; Copy Python bot
    File /r "..\..\dist\GridBotChuck\*.*"

    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\GridBot Chuck.exe"
    CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\GridBot Chuck.exe"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
    RMDir /r "$INSTDIR"
SectionEnd
"""

    nsis_script = INSTALLER_DIR / "installer.nsi"
    nsis_script.write_text(nsis_content)
    print(f"Created NSIS script: {nsis_script}")

def main():
    """Main build process."""
    print(r"""
    ╔═══════════════════════════════════════╗
    ║   GridBot Chuck - Windows Builder     ║
    ╚═══════════════════════════════════════╝
    """)

    try:
        # Step 1: Clean previous builds
        clean_build_dirs()

        # Step 2: Bundle Python bot
        bundle_python_bot()

        # Step 3: Build Electron app
        build_electron_app()

        # Step 4: Create installer
        create_nsis_installer()

        print_step("✅ BUILD COMPLETE!")
        print(f"Installer location: {DIST_DIR / 'GridBotChuck-Setup-1.0.0.exe'}")
        print("\nNext steps:")
        print("1. Test the installer on a clean Windows machine")
        print("2. Run the installed app and complete setup wizard")
        print("3. Verify bot starts and connects properly")

    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
