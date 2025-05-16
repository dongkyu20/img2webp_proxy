import subprocess
import platform
import time
import signal
import os
import sys

# set mitmproxy
MITM_HOST = "127.0.0.1"
MITM_PORT = "8227"

# get current script path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

MITM_SCRIPT_PATH = os.path.join(CURRENT_DIR, "img_intercept_storelog.py")
MITMDUMP_PATH = os.path.join(CURRENT_DIR, "mitmdump")
if not os.path.exists(MITMDUMP_PATH):
    MITMDUMP_PATH = "mitmdump"  # fallback to system PATH if not found in bundle

# --- OS별 프록시 설정 함수 ---

# macOS proxy setting
def get_active_network_service_mac():
    try:
        # find active network service (Wi-Fi or Ethernet)
        services_output = subprocess.check_output(['networksetup', '-listallnetworkservices']).decode().strip()
        services = services_output.split('\n')[1:] # first line is header, so exclude
        for service in services:
            if not service: continue
            try:
                info = subprocess.check_output(['networksetup', '-getinfo', service]).decode()
                if "IP address:" in info and "none" not in info.split("IP address:")[1].split("\n")[0].lower() \
                   and "<not connected>" not in info.lower():
                    hw_port_info = subprocess.check_output(['networksetup', '-listnetworkserviceorder']).decode()
                    if f"(Hardware Port: {service}," in hw_port_info or f"(Device: en" in hw_port_info and service in hw_port_info: # Wi-Fi는 보통 en0, en1 등으로 표시됨
                         print(f"Active network service detected: {service}")
                         return service
            except subprocess.CalledProcessError:
                continue
    except Exception as e:
        print(f"Active network service detection error: {e}")

    # default value or ask user
    default_service = "Wi-Fi" # or "Ethernet"
    print(f"Active network service not detected. Using default service: '{default_service}'")
    print("You can check the correct service name in 'Network Settings' or using the `networksetup -listallnetworkservices` command.")
    return default_service


def set_macos_proxy(service_name):
    if not service_name:
        print("macOS network service name not found. Proxy cannot be set.")
        return
    try:
        subprocess.run(['networksetup', '-setwebproxy', service_name, MITM_HOST, MITM_PORT], check=True)
        subprocess.run(['networksetup', '-setsecurewebproxy', service_name, MITM_HOST, MITM_PORT], check=True)
        print(f"macOS proxy set ({service_name}): {MITM_HOST}:{MITM_PORT}")
    except Exception as e:
        print(f"macOS proxy set error ({service_name}): {e}")
        print("Permission issue may occur. Run as sudo if needed.")

def unset_macos_proxy(service_name):
    if not service_name:
        print("macOS network service name not found. Proxy cannot be unset.")
        return
    try:
        subprocess.run(['networksetup', '-setwebproxystate', service_name, 'off'], check=True)
        subprocess.run(['networksetup', '-setsecurewebproxystate', service_name, 'off'], check=True)
        print(f"macOS proxy unset ({service_name}).")
    except Exception as e:
        print(f"macOS proxy unset error ({service_name}): {e}")

# Linux (GNOME) proxy setting
def set_linux_gnome_proxy():
    try:
        # GNOME environment proxy setting (gsettings usage)
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy', 'mode', "'manual'"], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy.http', 'host', f"'{MITM_HOST}'"], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy.http', 'port', MITM_PORT], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy.https', 'host', f"'{MITM_HOST}'"], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy.https', 'port', MITM_PORT], check=True)
        # some applications may also check environment variables, so provide instructions if needed
        print(f"Linux (GNOME) proxy set: {MITM_HOST}:{MITM_PORT}")
        print("Some programs running in terminal may also use environment variables:")
        print(f"  export http_proxy=http://{MITM_HOST}:{MITM_PORT}")
        print(f"  export https_proxy=http://{MITM_HOST}:{MITM_PORT}")
        print(f"  export no_proxy=localhost,127.0.0.1")
    except Exception as e:
        print(f"Linux (GNOME) proxy set error: {e}")
        print("gsettings command not found or GNOME desktop environment not detected.")

def unset_linux_gnome_proxy():
    try:
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy', 'mode', "'none'"], check=True)
        print("Linux (GNOME) proxy unset.")
        print("If environment variables were set, unset them in the terminal:")
        print(f"  unset http_proxy")
        print(f"  unset https_proxy")
        print(f"  unset no_proxy")
    except Exception as e:
        print(f"Linux (GNOME) proxy unset error: {e}")

# --- Main logic ---
mitm_process = None
original_sigint_handler = signal.getsignal(signal.SIGINT)
active_mac_service = None # macOS active service name

def cleanup_and_exit(signum, frame):
    global mitm_process, active_mac_service
    print("\nReceived termination signal. Starting cleanup...")

    current_os = platform.system()
    if current_os == "Windows":
        unset_windows_proxy()
    elif current_os == "Darwin": # macOS
        if active_mac_service:
            unset_macos_proxy(active_mac_service)
        else: # script started without active_mac_service
            temp_service = get_active_network_service_mac() # try again
            unset_macos_proxy(temp_service)
    elif current_os == "Linux":
        # GNOME environment check (gsettings command existence)
        try:
            subprocess.run(['gsettings', '--version'], capture_output=True, check=True, timeout=1)
            unset_linux_gnome_proxy()
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print("gsettings not found or response timeout. Skipping GNOME proxy unset.")
            print("If using a different desktop environment (e.g., KDE) or manually set environment variables, please unset them manually.")

    if mitm_process and mitm_process.poll() is None:
        print("mitmproxy process terminating...")
        if platform.system() == "Windows":
            mitm_process.send_signal(signal.CTRL_C_EVENT) # Windows에서는 Ctrl+C 이벤트
        else:
            mitm_process.send_signal(signal.SIGINT) # Unix 계열에서는 SIGINT
        try:
            mitm_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("mitmproxy process terminated abnormally. Forcing termination...")
            mitm_process.kill()
        print("mitmproxy process terminated.")

    # Restore original SIGINT handler (optional, script will exit here)
    signal.signal(signal.SIGINT, original_sigint_handler)
    print("All cleanup completed. Exiting program.")
    sys.exit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup_and_exit) # Ctrl+C processing
    signal.signal(signal.SIGTERM, cleanup_and_exit) # Optional signal handler for termination

    current_os = platform.system()

    # mitmproxy command configuration
    mitm_command = [MITMDUMP_PATH, "-p", MITM_PORT] # mitmdump or mitmweb
    if MITM_SCRIPT_PATH and os.path.exists(MITM_SCRIPT_PATH):
        mitm_command.extend(["-s", MITM_SCRIPT_PATH])
    elif MITM_SCRIPT_PATH:
        print(f"Warning: mitmproxy script '{MITM_SCRIPT_PATH}' not found.")
    
    print(f"Using mitmdump path: {MITMDUMP_PATH}")
    print(f"Using script path: {MITM_SCRIPT_PATH}")

    try:
        # mitmproxy start
        print(f"mitmproxy starting (command: {' '.join(mitm_command)})...")
        # Windows에서는 Popen에 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP 추가하여 Ctrl+C가 부모에도 영향 없도록
        popen_kwargs = {}
        if platform.system() == "Windows":
            popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP

        mitm_process = subprocess.Popen(mitm_command, **popen_kwargs)
        time.sleep(3) # mitmproxy가 시작될 시간을 줌

        if mitm_process.poll() is not None:
            print("mitmproxy process failed to start. Please check the error.")
            sys.exit()
        print("mitmproxy process started.")

        #   2. System proxy settings
        if current_os == "Windows":
            set_windows_proxy()
        elif current_os == "Darwin": # macOS
            active_mac_service = get_active_network_service_mac()
            set_macos_proxy(active_mac_service)
        elif current_os == "Linux":
            # GNOME environment check
            try:
                subprocess.run(['gsettings', '--version'], capture_output=True, check=True, timeout=1)
                set_linux_gnome_proxy()
            except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                print("gsettings not found or response timeout. Skipping GNOME proxy set.")
                print("If using a different desktop environment (e.g., KDE) or manually set environment variables, please set them manually.")
                print("Many CLI tools use HTTP_PROXY, HTTPS_PROXY environment variables.")
                print(f"  Example: export http_proxy=http://{MITM_HOST}:{MITM_PORT}")
        else:
            print(f"Unsupported OS: {current_os}. Please set proxy manually.")

        print("\nmitmproxy process started. System proxy settings applied.")
        print("When done, close this window to terminate mitmproxy and restore proxy settings.")

        # mitmproxy wait until it exits (or until user presses Ctrl+C)
        mitm_process.wait() # mitmproxy itself exits, this script goes to cleanup stage

    except Exception as e: # KeyboardInterrupt except
        print(f"Error occurred: {e}")
    finally:
        # cleanup
        if mitm_process and mitm_process.poll() is None :
             cleanup_and_exit(None, None)
        elif not (signal.getsignal(signal.SIGINT) == cleanup_and_exit) :
             print("Main loop terminated before cleanup_and_exit handler was set. Attempting to restore proxy settings.")
             cleanup_and_exit(None, None)