#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_app.py - Build script for the Proxy GUI application
"""

import os
import sys
import subprocess
import platform
import shutil

def create_client_secret_instructions():
    """Create instructions for setting up Google OAuth credentials"""
    instructions_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GOOGLE_AUTH_SETUP.md")
    
    instructions = """# Google OAuth Setup Instructions

To use the Google authentication feature in this application, you need to create OAuth 2.0 credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Select "Desktop app" as the application type
6. Name your client ID (e.g., "Proxy GUI Client")
7. Click "Create"
8. Download the JSON file
9. Rename the downloaded file to `client_secret.json`
10. Place the file in the same directory as the application executable

The application will look for this file when you try to authenticate with Google.
"""
    
    with open(instructions_path, 'w') as f:
        f.write(instructions)
    
    print(f"Created Google OAuth setup instructions at: {instructions_path}")

def create_spec_file():
    """Create a PyInstaller spec file for the application"""
    spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy_gui.spec")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create the app icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Greenee_Icon.png")
    
    # Determine platform-specific settings
    if platform.system() == "Darwin":  # macOS
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{os.path.join(current_dir, "proxy_gui.py")}'],
    pathex=['{current_dir}'],
    binaries=[('mitmdump', '.')],
    datas=[
        ('{os.path.join(current_dir, "../../Greenee_Icon.png")}', '.'),
        ('{os.path.join(current_dir, "img_intercept_storelog.py")}', '.'),
        ('{os.path.join(current_dir, "file_exists.py")}', '.'),
        ('{os.path.join(current_dir, "mitmproxy-ca-cert.pem")}', '.'),
        ('{os.path.join(current_dir, "GOOGLE_AUTH_SETUP.md")}', '.'),
    ],
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={{}},
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
    name='Proxy GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{icon_path}',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Proxy GUI',
)

# Create macOS app bundle
app = BUNDLE(
    coll,
    name='Proxy GUI.app',
    icon='{icon_path}',
    bundle_identifier='com.ecarbon.proxygui',
    info_plist={{
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHumanReadableCopyright': '© 2025 eCarbon',
    }},
)
"""
    else:  # Windows/Linux
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{os.path.join(current_dir, "proxy_gui.py")}'],
    pathex=['{current_dir}'],
    binaries=[],
    datas=[
        ('{os.path.join(current_dir, "../../Greenee_Icon.png")}', '.'),
        ('{os.path.join(current_dir, "img_intercept_storelog.py")}', '.'),
        ('{os.path.join(current_dir, "file_exists.py")}', '.'),
        ('{os.path.join(current_dir, "mitmproxy-ca-cert.pem")}', '.'),
        ('{os.path.join(current_dir, "GOOGLE_AUTH_SETUP.md")}', '.'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'mitmproxy'
    ],
    hookspath=[],
    hooksconfig={{}},
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Proxy GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{icon_path}',
)
"""
    
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    print(f"Created PyInstaller spec file at: {spec_path}")
    return spec_path

def update_requirements():
    """Update requirements.txt with new dependencies"""
    req_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "requirements.txt")
    
    new_requirements = [
        "mitmproxy",
        "pillow",
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
        "requests",
        "codecarbon",
        "google-cloud-storage",
        "pyinstaller"
    ]
    
    # Read existing requirements if file exists
    existing_requirements = []
    if os.path.exists(req_path):
        with open(req_path, 'r') as f:
            existing_requirements = [line.strip() for line in f.readlines() if line.strip()]
    
    # Merge requirements (avoid duplicates)
    all_requirements = list(set(existing_requirements + new_requirements))
    all_requirements.sort()
    
    # Write updated requirements
    with open(req_path, 'w') as f:
        for req in all_requirements:
            f.write(f"{req}\n")
    
    print(f"Updated requirements.txt at: {req_path}")

def build_application():
    """Build the application using PyInstaller"""
    # Create instructions for Google OAuth setup
    create_client_secret_instructions()
    
    # Create spec file
    spec_path = create_spec_file()
    
    # Update requirements.txt
    update_requirements()
    
    # Run PyInstaller
    print("Building application with PyInstaller...")
    try:
        subprocess.run(["pyinstaller", spec_path], check=True)
        print("\nBuild completed successfully!")
        
        # Show output directory
        dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
        print(f"Application files are in: {dist_dir}")
        
        # Instructions for running
        print("\nTo run the application:")
        if platform.system() == "Darwin":  # macOS
            print(f"Open the 'Proxy GUI.app' in the dist folder")
        else:
            print(f"Run the 'Proxy GUI' executable in the dist folder")
        
        # Reminder about Google OAuth credentials
        print("\nIMPORTANT: Before using the application, you need to set up Google OAuth credentials.")
        print("See the GOOGLE_AUTH_SETUP.md file for instructions.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error building application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_application()
