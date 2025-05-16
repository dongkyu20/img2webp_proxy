# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['/Users/admin/Documents/DomainModify_Proxy/src/client/proxy_gui.py'],
    pathex=['/Users/admin/Documents/DomainModify_Proxy/src/client'],
    binaries=[
        # Include the actual mitmdump binary, not just the script
        ('/Users/admin/Documents/DomainModify_Proxy/venv/bin/mitmdump', '.'),
    ],
    datas=[
        ('/Users/admin/Documents/DomainModify_Proxy/src/client/../../Greenee_Icon.png', '.'),
        ('/Users/admin/Documents/DomainModify_Proxy/src/client/img_intercept_storelog.py', '.'),
        ('/Users/admin/Documents/DomainModify_Proxy/src/client/file_exists.py', '.'),
        ('/Users/admin/Documents/DomainModify_Proxy/src/client/mitmproxy-ca-cert.pem', '.'),
        ('/Users/admin/Documents/DomainModify_Proxy/src/client/GOOGLE_AUTH_SETUP.md', '.'),
        ('/Users/admin/Documents/DomainModify_Proxy/src/client/woven-province-411903-b1b12d94b3ac.json', '.'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'mitmproxy',
        'mitmproxy.tools',
        'mitmproxy.tools.main',
        'mitmproxy.tools.dump',
        'mitmproxy.addons',
        'mitmproxy.http',
        'mitmproxy.net',
        'mitmproxy.proxy',
        'mitmproxy.connections',
        'mitmproxy.contentviews',
        'mitmproxy.coretypes',
        'mitmproxy.certs',
        'mitmproxy.flow',
        'mitmproxy.io',
        'mitmproxy.log',
        'mitmproxy.master',
        'mitmproxy.options',
        'mitmproxy.optmanager',
        'mitmproxy.platform',
        'mitmproxy.proxy.config',
        'mitmproxy.proxy.layers',
        'mitmproxy.proxy.mode_specs',
        'mitmproxy.proxy.protocol',
        'mitmproxy.proxy.server',
        'mitmproxy.utils',
        'mitmproxy.websocket',
        'google.cloud',
        'google.cloud.storage',
        'google.oauth2',
        'google.oauth2.service_account',
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
    icon='/Users/admin/Documents/DomainModify_Proxy/src/client/../../Greenee_Icon.png',
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
    icon='/Users/admin/Documents/DomainModify_Proxy/src/client/../../Greenee_Icon.png',
    bundle_identifier='com.ecarbon.proxygui',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHumanReadableCopyright': '© 2025 eCarbon',
    },
)
