#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
proxy_gui.py - GUI application for controlling mitmproxy with Google authentication
"""

import os
import sys
import platform
import subprocess
import threading
import time
import signal
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import json
from PIL import Image, ImageTk
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Import from project files
from set_proxy_addr import (
    MITM_HOST, MITM_PORT, MITMDUMP_PATH, MITM_SCRIPT_PATH,
    get_active_network_service_mac, set_macos_proxy, unset_macos_proxy,
    set_linux_gnome_proxy, unset_linux_gnome_proxy
)

# Google OAuth configuration
SCOPES = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

# 여러 경로에서 client_secret.json 파일 찾기
def find_credentials_file():
    # 가능한 경로 목록
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secret.json'),  # 스크립트 폴더
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'client_secret.json'),  # 프로젝트 루트 폴더
        os.path.abspath('client_secret.json'),  # 현재 작업 디렉토리
        os.path.join(os.path.dirname(sys.executable), 'client_secret.json'),  # 실행 파일 폴더 (PyInstaller)
    ]
    
    # 존재하는 첫 번째 경로 반환
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found credentials file at: {path}")
            return path
    
    print("Credentials file not found in any of the expected locations")
    return None

CREDENTIALS_FILE = find_credentials_file()
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.json')

class ProxyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Proxy Control Panel")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        # Set icon if available
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Greenee_Icon.png")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(False, photo)
        except Exception as e:
            print(f"Error loading icon: {e}")
            # Continue without icon
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Helvetica', 12))
        self.style.configure('TLabel', font=('Helvetica', 12))
        self.style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'))
        self.style.configure('Status.TLabel', font=('Helvetica', 12, 'bold'))
        self.style.configure('User.TLabel', font=('Helvetica', 10))
        
        # Variables
        self.proxy_active = False
        self.mitm_process = None
        self.active_service = None
        self.user_info = None
        self.authenticated = False
        
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.header_label = ttk.Label(self.main_frame, text="Proxy Control Panel", style='Header.TLabel')
        self.header_label.pack(pady=(0, 20))
        
        # Authentication section
        self.auth_frame = ttk.LabelFrame(self.main_frame, text="Authentication", padding=10)
        self.auth_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.auth_status_label = ttk.Label(self.auth_frame, text="Not authenticated", style='Status.TLabel')
        self.auth_status_label.pack(pady=(0, 10))
        
        self.auth_button = ttk.Button(self.auth_frame, text="Sign in with Google", command=self.authenticate)
        self.auth_button.pack(fill=tk.X)
        
        self.user_info_label = ttk.Label(self.auth_frame, text="", style='User.TLabel')
        self.user_info_label.pack(pady=(10, 0))
        
        # Proxy control section
        self.proxy_frame = ttk.LabelFrame(self.main_frame, text="Proxy Control", padding=10)
        self.proxy_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.status_label = ttk.Label(self.proxy_frame, text="Proxy: Inactive", style='Status.TLabel')
        self.status_label.pack(pady=(0, 10))
        
        self.toggle_button = ttk.Button(self.proxy_frame, text="Start Proxy", command=self.toggle_proxy)
        self.toggle_button.pack(fill=tk.X)
        self.toggle_button.state(['disabled'])  # Disabled until authenticated
        
        # Status log section
        self.log_frame = ttk.LabelFrame(self.main_frame, text="Status Log", padding=10)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(self.log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Set up clean exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Check for existing token
        self.check_existing_auth()
        
    def check_existing_auth(self):
        """Check if user is already authenticated"""
        if os.path.exists(TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_info(json.load(open(TOKEN_FILE)))
                if creds and creds.valid:
                    self.authenticated = True
                    self.get_user_info(creds)
                    self.update_auth_ui()
                    self.log("Authentication loaded from saved credentials")
                elif creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self.authenticated = True
                    self.get_user_info(creds)
                    self.update_auth_ui()
                    self.log("Authentication refreshed from saved credentials")
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
            except Exception as e:
                self.log(f"Error loading saved credentials: {e}")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
    
    def authenticate(self):
        """Authenticate with Google"""
        # 로그 출력으로 함수 호출 확인
        print("authenticate() 함수 호출됨")
        self.log("인증 시도 중...")
        
        # client_secret.json 파일 경로 확인
        if CREDENTIALS_FILE:
            self.log(f"인증 파일 경로: {CREDENTIALS_FILE}")
        else:
            self.log("인증 파일을 찾을 수 없습니다.")
        
        # Google 인증 시도
        if CREDENTIALS_FILE and os.path.exists(CREDENTIALS_FILE):
            try:
                self.log(f"Google 인증 파일 발견: {CREDENTIALS_FILE}")
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                
                self.authenticated = True
                self.get_user_info(creds)
                self.update_auth_ui()
                self.log("Google 인증 성공")
                return
            except Exception as e:
                self.log(f"Google 인증 오류: {e}")
                # 인증 실패 시 개발 모드로 진행
                self.log("개발 모드로 진행합니다.")
        else:
            self.log("Google 인증 파일이 없어 개발 모드로 진행합니다.")
        
        # 개발 모드 적용
        self.authenticated = True
        self.user_info = {"email": "dev@example.com", "name": "Development User"}
        self.update_auth_ui()
    
    def get_user_info(self, creds):
        """Get user information from Google API"""
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {creds.token}'}
            )
            self.user_info = response.json()
        except Exception as e:
            self.log(f"Error getting user info: {e}")
    
    def update_auth_ui(self):
        """Update the UI based on authentication status"""
        if self.authenticated and self.user_info:
            self.auth_status_label.config(text="Authenticated")
            self.auth_button.config(text="Sign out", command=self.sign_out)
            self.user_info_label.config(text=f"Email: {self.user_info.get('email', 'Unknown')}")
            self.toggle_button.state(['!disabled'])  # Enable proxy toggle
        else:
            self.auth_status_label.config(text="Not authenticated")
            self.auth_button.config(text="Sign in with Google", command=self.authenticate)
            self.user_info_label.config(text="")
            self.toggle_button.state(['disabled'])  # Disable proxy toggle
    
    def sign_out(self):
        """Sign out from Google"""
        # 로그 출력으로 함수 호출 확인
        print("sign_out() 함수 호출됨")
        self.log("로그아웃 시도 중...")
        
        # 토큰 파일 삭제
        if os.path.exists(TOKEN_FILE):
            try:
                os.remove(TOKEN_FILE)
                self.log("토큰 파일 삭제됨")
            except Exception as e:
                self.log(f"토큰 파일 삭제 오류: {e}")
        
        # 인증 상태 초기화
        self.authenticated = False
        self.user_info = None
        self.update_auth_ui()
        self.log("로그아웃 완료")
        
        # 프록시가 활성화되어 있으면 중지
        if self.proxy_active:
            self.log("프록시가 활성화되어 있어 중지합니다.")
            self.toggle_proxy()
    
    def toggle_proxy(self):
        """Toggle proxy on/off"""
        if not self.authenticated:
            messagebox.showwarning("Authentication Required", "Please sign in with Google first.")
            return
        
        if self.proxy_active:
            self.stop_proxy()
        else:
            self.start_proxy()
    
    def start_proxy(self):
        """Start the proxy"""
        if self.proxy_active:
            return

        try:
            # 현재 OS 확인
            current_os = platform.system()
            
            # Check if we're in a bundled app
            is_bundled = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
            
            # Get the base directory for resources
            if is_bundled and current_os == "Darwin":
                # For macOS .app bundle, try multiple locations
                possible_script_paths = [
                    os.path.join(os.path.dirname(sys.executable), "../Resources/img_intercept_storelog.py"),
                    os.path.join(os.path.dirname(sys.executable), "../Frameworks/img_intercept_storelog.py"),
                    os.path.join(os.path.dirname(sys.executable), "img_intercept_storelog.py"),
                    MITM_SCRIPT_PATH
                ]
                
                # Use the first script path that exists
                script_path = next((path for path in possible_script_paths if os.path.exists(path)), MITM_SCRIPT_PATH)
                self.log(f"Found script at: {script_path}")
                
                # Set base directory based on script location
                base_dir = os.path.dirname(script_path)
            else:
                # For development environment
                base_dir = os.path.dirname(os.path.abspath(__file__))
                script_path = MITM_SCRIPT_PATH
            
            # Try to find mitmdump in various locations
            possible_mitmdump_paths = [
                MITMDUMP_PATH,  # From set_proxy_addr.py
                os.path.join(base_dir, "mitmdump"),  # In the same directory as the script
                "/usr/local/bin/mitmdump",  # Common location on macOS
                "/opt/homebrew/bin/mitmdump",  # Homebrew on Apple Silicon
                "mitmdump",  # In system PATH
            ]
            
            # Use the first mitmdump that exists
            mitmdump_path = next((path for path in possible_mitmdump_paths if os.path.exists(path) or path == "mitmdump"), MITMDUMP_PATH)
            
            # mitmdump 명령어 구성
            mitm_command = [mitmdump_path, "-p", MITM_PORT]
            if os.path.exists(script_path):
                mitm_command.extend(["-s", script_path])
                self.log(f"Using script: {script_path}")
            else:
                self.log(f"Warning: Script not found at {script_path}")
            
            self.log(f"Starting mitmproxy: {' '.join(mitm_command)}")
            
            # subprocess로 mitmdump 실행
            popen_kwargs = {}
            if current_os == "Windows":
                popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            
            # Add environment variables to help mitmproxy find its dependencies
            env = os.environ.copy()
            if is_bundled:
                env['PYTHONPATH'] = base_dir
                if current_os == "Darwin":
                    # For macOS, add the Frameworks directory to PATH
                    env['PATH'] = f"{base_dir}:{env.get('PATH', '')}" 
            
            self.mitm_process = subprocess.Popen(mitm_command, env=env, **popen_kwargs)
            time.sleep(3)  # 프록시가 시작될 시간을 줌
            
            if self.mitm_process.poll() is not None:
                self.log("mitmproxy failed to start")
                messagebox.showerror("Error", "Failed to start mitmproxy")
                return
            
            # 시스템 프록시 설정
            if current_os == "Darwin":  # macOS
                self.active_service = get_active_network_service_mac()
                set_macos_proxy(self.active_service)
            elif current_os == "Windows":
                set_windows_proxy()
            elif current_os == "Linux":
                set_linux_gnome_proxy()
            
            self.proxy_active = True
            self.status_label.config(text="Proxy: Active")
            self.toggle_button.config(text="Stop Proxy")
            self.log("Proxy started successfully")
            
        except Exception as e:
            self.log(f"Error starting proxy: {e}")
    
    def stop_proxy(self):
        """Stop the proxy"""
        if not self.proxy_active:
            return
        
        try:
            # Stop mitmproxy
            if self.mitm_process and self.mitm_process.poll() is None:
                self.log("Stopping mitmproxy...")
                if platform.system() == "Windows":
                    self.mitm_process.send_signal(signal.CTRL_C_EVENT)
                else:
                    self.mitm_process.send_signal(signal.SIGINT)
                
                try:
                    self.mitm_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.log("mitmproxy termination timeout. Forcing termination...")
                    self.mitm_process.kill()
            
            # Unset system proxy
            current_os = platform.system()
            if current_os == "Darwin" and self.active_service:  # macOS
                unset_macos_proxy(self.active_service)
            elif current_os == "Linux":
                try:
                    unset_linux_gnome_proxy()
                except:
                    self.log("Failed to unset Linux proxy. Please check manually.")
            
            # Update UI
            self.proxy_active = False
            self.status_label.config(text="Proxy: Inactive")
            self.toggle_button.config(text="Stop Proxy")
            self.log("Proxy stopped successfully")
            
        except Exception as e:
            self.log(f"Error stopping proxy: {e}")
            messagebox.showerror("Error", f"Failed to stop proxy: {e}")
    
    def log(self, message):
        """Add message to log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        print(log_message.strip())  # Also print to console
    
    def on_close(self):
        """Handle window close event"""
        if self.proxy_active:
            if messagebox.askyesno("Confirm Exit", "Proxy is still active. Do you want to stop it and exit?"):
                self.stop_proxy()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = ProxyGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
