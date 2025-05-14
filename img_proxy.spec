# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Image-Proxy tool based on mitmproxy.
Run with:  pyinstaller -y img_proxy.spec
The resulting bundled application will be located in ./dist/img_proxy
"""

block_cipher = None

# Main analysis for the proxy application
# NOTE: we keep paths relative so that the command can be executed from the project root.
a = Analysis(
    ["src/client/set_proxy_addr.py"],          # Entry-point script
    pathex=["."],
    binaries=[
        # Include mitmdump binary if possible
        # Note: This might not work on all systems and may require manual adjustment
        ("/Users/admin/Documents/DomainModify_Proxy/venv/bin/mitmdump", "."),
    ],                                 # Try to include mitmdump binary
    datas=[                                      # Extra data / scripts required at runtime
        ("src/client/img_intercept_storelog.py", "."),
        ("src/client/file_exists.py", "."),
        ("src/client/install_cert.py", "."),    # Certificate installation helper script
        ("woven-province-411903-b1b12d94b3ac.json", "."),
        ("cdn_file_list.txt", "."),             # Include the CDN file list
        ("smaller_original_images.txt", "."),   # Include the smaller images list
    ],
    hiddenimports=[
        "mitmproxy",                          # Include full mitmproxy package
        "mitmproxy.addons",                    # mitmproxy dynamically imports its addons package
        "mitmproxy.connections",
        "mitmproxy.proxy",
        "mitmproxy.tools",
        "mitmproxy.master",
        "google.cloud",                        # Ensure Google Cloud Storage modules are included
        "google.cloud.storage",
        "google.api_core",
        "codecarbon",                         # Include carbon emissions tracking library
        "cryptography",
        "pyOpenSSL",
        "certifi",
        "requests",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

# Separate analysis for the certificate installer
b = Analysis(
    ["src/client/install_cert.py"],          # Certificate installer script
    pathex=["."],
    binaries=[
        # Include mitmdump binary if possible (for certificate installation)
        ("/Users/admin/Documents/DomainModify_Proxy/venv/bin/mitmdump", "."),
    ],
    datas=[
        ("mitmproxy-ca-cert.pem", "."),      # Include the certificate file
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

# Python byte-code archives
pyz_a = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
pyz_b = PYZ(b.pure, b.zipped_data, cipher=block_cipher)

# Certificate installer executable
cert_installer = EXE(
    pyz_b,
    b.scripts,
    [],
    exclude_binaries=True,
    name="install_cert",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# Main executable
exe = EXE(
    pyz_a,
    a.scripts,
    [],                      # No additional modules passed explicitly
    exclude_binaries=True,
    name="img_proxy",       # Output binary name (without extension)
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,            # Leave this True so stdout/stderr are visible.
    disable_windowed_traceback=False,
)

# Collect step – bundle exe + data
coll = COLLECT(
    exe,
    cert_installer,  # Include certificate installer executable
    a.binaries,
    a.zipfiles,
    a.datas,
    b.binaries,
    b.zipfiles,
    b.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="img_proxy",
)