#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Certificate installation helper script for the Image Proxy application.
This script helps users download and install the mitmproxy certificate.
"""

import os
import platform
import subprocess
import webbrowser
import time
import sys
import shutil

def main():
    print("=" * 60)
    print("이미지 프록시 인증서 설치 도우미")
    print("=" * 60)
    print("\n이 도구는 mitmproxy 인증서를 다운로드하고 설치하는 과정을 안내합니다.")
    print("인증서는 HTTPS 트래픽을 검사하기 위해 필요합니다.\n")
    
    # 인증서 다운로드 안내
    print("1. 인증서 다운로드")
    print("-" * 60)
    print("아래 URL에서 mitmproxy 인증서를 다운로드할 수 있습니다:")
    print("http://mitm.it")
    
    # 브라우저에서 mitm.it 열기
    open_browser = input("\n브라우저에서 mitm.it 페이지를 열까요? (y/n): ").lower().strip()
    if open_browser == 'y':
        # 먼저 mitmproxy를 실행해야 인증서 다운로드 페이지가 제대로 작동함
        print("\nmitmproxy를 잠시 실행합니다. 인증서 다운로드를 위해 필요합니다...")
        
        # 현재 스크립트의 디렉토리 경로 가져오기
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        try:
            # mitmdump 경로 찾기
            mitmdump_path = "mitmdump"
            
            # 패키지 내부에서 실행되는지 확인
            if getattr(sys, 'frozen', False):
                # PyInstaller로 빌드된 애플리케이션인 경우
                base_dir = os.path.dirname(sys.executable)
                
                # 디렉토리에서 mitmdump 찾기
                possible_paths = [
                    os.path.join(base_dir, "mitmdump"),
                    os.path.join(base_dir, "_internal", "mitmdump")
                ]
                
                if platform.system() == "Windows":
                    possible_paths = [
                        os.path.join(base_dir, "mitmdump.exe"),
                        os.path.join(base_dir, "_internal", "mitmdump.exe")
                    ]
                
                for path in possible_paths:
                    if os.path.exists(path) and os.access(path, os.X_OK):
                        mitmdump_path = path
                        break
            
            # 시스템 PATH에서 찾기
            if mitmdump_path == "mitmdump":
                mitmdump_in_path = shutil.which("mitmdump")
                if mitmdump_in_path:
                    mitmdump_path = mitmdump_in_path
            
            print(f"Using mitmdump from: {mitmdump_path}")
            
            # mitmproxy 실행 (백그라운드에서)
            mitm_process = None
            if platform.system() == "Windows":
                mitm_process = subprocess.Popen([mitmdump_path, "-p", "8227"], 
                                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                mitm_process = subprocess.Popen([mitmdump_path, "-p", "8227"], 
                                               stdout=subprocess.DEVNULL, 
                                               stderr=subprocess.DEVNULL)
            
            # 잠시 대기하여 mitmproxy가 시작되도록 함
            time.sleep(2)
            
            # 브라우저 열기
            webbrowser.open("http://mitm.it")
            
            print("\n브라우저에서 mitm.it 페이지가 열렸습니다.")
            print("운영체제에 맞는 인증서를 다운로드하고 설치하세요.")
            
            # 사용자가 인증서를 다운로드하고 설치할 시간을 줌
            input("\n인증서 설치가 완료되면 Enter 키를 누르세요...")
            
        finally:
            # mitmproxy 프로세스 종료
            if mitm_process:
                mitm_process.terminate()
                try:
                    mitm_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    mitm_process.kill()
    
    # OS별 인증서 설치 안내
    current_os = platform.system()
    print("\n2. 인증서 설치 안내")
    print("-" * 60)
    
    if current_os == "Darwin":  # macOS
        print("macOS 인증서 설치 방법:")
        print("1. 다운로드한 .pem 파일을 더블클릭하여 '키체인 접근'에서 엽니다.")
        print("2. 인증서가 '로그인' 키체인에 추가됩니다.")
        print("3. 인증서를 더블클릭하고 '신뢰' 섹션을 확장합니다.")
        print("4. '이 인증서 사용 시'에서 '항상 신뢰'를 선택합니다.")
        print("5. 키체인 접근을 닫으면 변경사항이 저장됩니다.")
    
    elif current_os == "Windows":
        print("Windows 인증서 설치 방법:")
        print("1. 다운로드한 .p12 파일을 더블클릭합니다.")
        print("2. '현재 사용자'를 선택하고 '다음'을 클릭합니다.")
        print("3. 파일 경로를 확인하고 '다음'을 클릭합니다.")
        print("4. 암호 입력 없이 '다음'을 클릭합니다.")
        print("5. '인증서 종류에 따라 인증서 저장소 자동으로 선택'을 선택하고 '다음'을 클릭합니다.")
        print("6. '마침'을 클릭하여 설치를 완료합니다.")
    
    elif current_os == "Linux":
        print("Linux 인증서 설치 방법:")
        print("Linux 배포판에 따라 인증서 설치 방법이 다릅니다.")
        print("일반적인 방법:")
        print("1. 다운로드한 .pem 파일을 /usr/local/share/ca-certificates/ 디렉토리에 .crt 확장자로 복사합니다.")
        print("   sudo cp mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt")
        print("2. 인증서 데이터베이스를 업데이트합니다.")
        print("   sudo update-ca-certificates")
        print("\n브라우저별 설정이 추가로 필요할 수 있습니다.")
    
    print("\n인증서 설치가 완료되었습니다. 이제 이미지 프록시 프로그램을 실행할 수 있습니다.")
    print("=" * 60)
    
    input("\n종료하려면 Enter 키를 누르세요...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n프로그램이 사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n오류가 발생했습니다: {e}")
        sys.exit(1)
