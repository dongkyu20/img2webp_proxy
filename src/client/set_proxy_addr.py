import subprocess
import platform
import time
import signal
import os

# mitmproxy 설정
MITM_HOST = "127.0.0.1"
MITM_PORT = "8227"
MITM_SCRIPT_PATH = "src/client/img_intercept_storelog.py"  # mitmproxy 애드온 스크립트 경로 (없으면 None 또는 빈 문자열)

# --- OS별 프록시 설정 함수 ---

# Windows용 프록시 설정/해제
def set_windows_proxy():
    try:
        # 프록시 활성화 및 서버 설정
        subprocess.run(['reg', 'add', r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings", '/v', 'ProxyEnable', '/t', 'REG_DWORD', '/d', '1', '/f'], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['reg', 'add', r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings", '/v', 'ProxyServer', '/t', 'REG_SZ', '/d', f'{MITM_HOST}:{MITM_PORT}', '/f'], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        # 변경사항 즉시 적용 (일부 앱에서는 재시작 필요할 수 있음)
        subprocess.run(['rundll32.exe', 'inetcpl.cpl,ClearMyTracksByProcess', '8'], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print(f"Windows 프록시 설정: {MITM_HOST}:{MITM_PORT}")
    except Exception as e:
        print(f"Windows 프록시 설정 오류: {e}")
        print("관리자 권한으로 실행해야 할 수 있습니다.")

def unset_windows_proxy():
    try:
        # 프록시 비활성화
        subprocess.run(['reg', 'add', r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings", '/v', 'ProxyEnable', '/t', 'REG_DWORD', '/d', '0', '/f'], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        # 변경사항 즉시 적용
        subprocess.run(['rundll32.exe', 'inetcpl.cpl,ClearMyTracksByProcess', '8'], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print("Windows 프록시 설정 해제됨.")
    except Exception as e:
        print(f"Windows 프록시 해제 오류: {e}")

# macOS용 프록시 설정/해제
def get_active_network_service_mac():
    try:
        # 활성 네트워크 서비스 찾기 (Wi-Fi 또는 Ethernet 등)
        services_output = subprocess.check_output(['networksetup', '-listallnetworkservices']).decode().strip()
        services = services_output.split('\n')[1:] # 첫 줄은 헤더이므로 제외
        for service in services:
            if not service: continue
            try:
                # 실제 활성화된 IP가 할당된 서비스를 찾으려 시도
                info = subprocess.check_output(['networksetup', '-getinfo', service]).decode()
                if "IP address:" in info and "none" not in info.split("IP address:")[1].split("\n")[0].lower() \
                   and "<not connected>" not in info.lower(): # 추가적인 연결 상태 확인
                    # 'Hardware Port'를 확인하여 실제 활성화된 포트인지 한번 더 가늠
                    hw_port_info = subprocess.check_output(['networksetup', '-listnetworkserviceorder']).decode()
                    if f"(Hardware Port: {service}," in hw_port_info or f"(Device: en" in hw_port_info and service in hw_port_info: # Wi-Fi는 보통 en0, en1 등으로 표시됨
                         print(f"활성 네트워크 서비스 감지: {service}")
                         return service
            except subprocess.CalledProcessError:
                continue # 해당 서비스 정보를 가져올 수 없는 경우 (예: 비활성 인터페이스)
    except Exception as e:
        print(f"활성 네트워크 서비스 감지 중 오류: {e}")

    # 기본값 또는 사용자에게 문의
    default_service = "Wi-Fi" # 또는 "Ethernet"
    print(f"활성 네트워크 서비스를 자동으로 감지하지 못했습니다. '{default_service}'를 기본값으로 사용합니다.")
    print("정확한 서비스명은 '네트워크 환경설정'에서 확인하거나 `networksetup -listallnetworkservices` 명령으로 확인하세요.")
    return default_service


def set_macos_proxy(service_name):
    if not service_name:
        print("macOS 네트워크 서비스 이름을 찾을 수 없어 프록시를 설정할 수 없습니다.")
        return
    try:
        subprocess.run(['networksetup', '-setwebproxy', service_name, MITM_HOST, MITM_PORT], check=True)
        subprocess.run(['networksetup', '-setsecurewebproxy', service_name, MITM_HOST, MITM_PORT], check=True)
        print(f"macOS 프록시 설정 ({service_name}): {MITM_HOST}:{MITM_PORT}")
    except Exception as e:
        print(f"macOS 프록시 설정 오류 ({service_name}): {e}")
        print("권한 문제일 수 있습니다. 필요한 경우 스크립트를 sudo로 실행하세요.")

def unset_macos_proxy(service_name):
    if not service_name:
        print("macOS 네트워크 서비스 이름을 찾을 수 없어 프록시를 해제할 수 없습니다.")
        return
    try:
        subprocess.run(['networksetup', '-setwebproxystate', service_name, 'off'], check=True)
        subprocess.run(['networksetup', '-setsecurewebproxystate', service_name, 'off'], check=True)
        print(f"macOS 프록시 설정 해제됨 ({service_name}).")
    except Exception as e:
        print(f"macOS 프록시 해제 오류 ({service_name}): {e}")

# Linux (GNOME)용 프록시 설정/해제
def set_linux_gnome_proxy():
    try:
        # GNOME 환경의 프록시 설정 (gsettings 사용)
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy', 'mode', "'manual'"], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy.http', 'host', f"'{MITM_HOST}'"], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy.http', 'port', MITM_PORT], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy.https', 'host', f"'{MITM_HOST}'"], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy.https', 'port', MITM_PORT], check=True)
        # 일부 애플리케이션은 환경 변수도 확인하므로, 필요시 설정 안내
        print(f"Linux (GNOME) 프록시 설정: {MITM_HOST}:{MITM_PORT}")
        print("터미널에서 실행되는 일부 프로그램은 환경 변수 설정을 따릅니다:")
        print(f"  export http_proxy=http://{MITM_HOST}:{MITM_PORT}")
        print(f"  export https_proxy=http://{MITM_HOST}:{MITM_PORT}")
        print(f"  export no_proxy=localhost,127.0.0.1")
    except Exception as e:
        print(f"Linux (GNOME) 프록시 설정 오류: {e}")
        print("gsettings 명령어를 사용할 수 없거나, GNOME 데스크탑 환경이 아닐 수 있습니다.")

def unset_linux_gnome_proxy():
    try:
        subprocess.run(['gsettings', 'set', 'org.gnome.system.proxy', 'mode', "'none'"], check=True)
        print("Linux (GNOME) 프록시 설정 해제됨.")
        print("환경 변수를 설정했다면, 터미널에서 해제하세요:")
        print(f"  unset http_proxy")
        print(f"  unset https_proxy")
        print(f"  unset no_proxy")
    except Exception as e:
        print(f"Linux (GNOME) 프록시 해제 오류: {e}")

# --- 메인 로직 ---
mitm_process = None
original_sigint_handler = signal.getsignal(signal.SIGINT)
active_mac_service = None # macOS에서 사용될 활성 서비스 이름

def cleanup_and_exit(signum, frame):
    global mitm_process, active_mac_service
    print("\n종료 신호 수신. 정리 작업을 시작합니다...")

    current_os = platform.system()
    if current_os == "Windows":
        unset_windows_proxy()
    elif current_os == "Darwin": # macOS
        if active_mac_service:
            unset_macos_proxy(active_mac_service)
        else: # 스크립트 시작 시 active_mac_service를 못찾은 경우를 대비
            temp_service = get_active_network_service_mac() # 다시 한번 시도
            unset_macos_proxy(temp_service)
    elif current_os == "Linux":
        # GNOME 환경인지 간단히 확인 (gsettings 명령어 존재 여부)
        try:
            subprocess.run(['gsettings', '--version'], capture_output=True, check=True, timeout=1)
            unset_linux_gnome_proxy()
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print("gsettings를 찾을 수 없거나 응답이 없어 GNOME 프록시 해제를 건너<0xEB><0x81>니다.")
            print("다른 데스크탑 환경(KDE 등)을 사용 중이거나 환경 변수를 직접 설정했다면 수동으로 해제해야 합니다.")

    if mitm_process and mitm_process.poll() is None:
        print("mitmproxy 프로세스를 종료합니다...")
        if platform.system() == "Windows":
            mitm_process.send_signal(signal.CTRL_C_EVENT) # Windows에서는 Ctrl+C 이벤트
        else:
            mitm_process.send_signal(signal.SIGINT) # Unix 계열에서는 SIGINT
        try:
            mitm_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("mitmproxy가 정상적으로 종료되지 않아 강제 종료합니다.")
            mitm_process.kill()
        print("mitmproxy가 종료되었습니다.")

    # 원래 SIGINT 핸들러 복원 (선택 사항, 스크립트가 여기서 종료되므로)
    signal.signal(signal.SIGINT, original_sigint_handler)
    print("모든 정리 작업 완료. 프로그램을 종료합니다.")
    exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup_and_exit) # Ctrl+C 처리기 등록
    signal.signal(signal.SIGTERM, cleanup_and_exit) # 종료 신호 처리기 등록 (선택 사항)

    current_os = platform.system()

    # mitmproxy 실행 명령어 구성
    mitm_command = ["mitmdump", "-p", MITM_PORT] # mitmproxy 또는 mitmweb으로 변경 가능
    if MITM_SCRIPT_PATH and os.path.exists(MITM_SCRIPT_PATH):
        mitm_command.extend(["-s", MITM_SCRIPT_PATH])
    elif MITM_SCRIPT_PATH:
        print(f"경고: mitmproxy 스크립트 '{MITM_SCRIPT_PATH}'를 찾을 수 없습니다.")

    try:
        # 1. mitmproxy 시작
        print(f"mitmproxy를 시작합니다 (명령어: {' '.join(mitm_command)})...")
        # Windows에서는 Popen에 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP 추가하여 Ctrl+C가 부모에도 영향 없도록
        popen_kwargs = {}
        if platform.system() == "Windows":
            popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP

        mitm_process = subprocess.Popen(mitm_command, **popen_kwargs)
        time.sleep(3) # mitmproxy가 시작될 시간을 줌

        if mitm_process.poll() is not None:
            print("mitmproxy 시작에 실패했습니다. 오류를 확인하세요.")
            exit(1)
        print("mitmproxy가 실행 중입니다.")

        # 2. 시스템 프록시 설정
        if current_os == "Windows":
            set_windows_proxy()
        elif current_os == "Darwin": # macOS
            active_mac_service = get_active_network_service_mac()
            set_macos_proxy(active_mac_service)
        elif current_os == "Linux":
            # GNOME 환경인지 간단히 확인
            try:
                subprocess.run(['gsettings', '--version'], capture_output=True, check=True, timeout=1)
                set_linux_gnome_proxy()
            except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                print("gsettings를 찾을 수 없거나 응답이 없습니다. GNOME 프록시 설정을 건너<0xEB><0x81>니다.")
                print("다른 데스크탑 환경(KDE 등)을 사용 중이라면 해당 환경에 맞는 프록시 설정 명령어를 사용해야 합니다.")
                print("많은 CLI 도구들은 HTTP_PROXY, HTTPS_PROXY 환경 변수를 사용합니다.")
                print(f"  예: export http_proxy=http://{MITM_HOST}:{MITM_PORT}")
        else:
            print(f"지원되지 않는 OS: {current_os}. 프록시를 수동으로 설정해주세요.")

        print("\nmitmproxy가 실행 중이고 시스템 프록시가 설정되었습니다.")
        print("작업 완료 후 이 창에서 Ctrl+C 를 누르면 mitmproxy가 종료되고 프록시 설정이 복원됩니다.")

        # mitmproxy가 종료될 때까지 대기 (또는 사용자가 Ctrl+C를 누를 때까지)
        mitm_process.wait() # mitmproxy 자체가 종료되면 이 스크립트도 정리 단계로 넘어감

    except Exception as e: # KeyboardInterrupt 외의 예외 처리
        print(f"오류 발생: {e}")
    finally:
        # mitm_process.wait()가 정상 종료되었거나, 예외가 발생했거나, 위에서 Ctrl+C 핸들러가 호출되지 않은 경우의 최종 정리
        # (일반적으로 cleanup_and_exit에서 대부분 처리됨)
        if mitm_process and mitm_process.poll() is None : # 아직 실행 중이라면
             cleanup_and_exit(None, None) # 강제 정리 호출
        elif not (signal.getsignal(signal.SIGINT) == cleanup_and_exit) : # 핸들러가 호출 안 된 경우
             print("메인 루프 외부에서 종료되어 프록시 복구를 시도합니다.")
             cleanup_and_exit(None, None) # 핸들러가 설정되기 전에 종료된 경우