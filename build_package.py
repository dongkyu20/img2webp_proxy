#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for the Image Proxy application.
This script automates the PyInstaller build process and ensures all necessary files are included.
"""

import os
import shutil
import subprocess
import platform
import sys
import site
from pathlib import Path

def ensure_file_exists(filename, create_empty=True):
    """Check if a file exists, and create an empty one if it doesn't."""
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found.")
        if create_empty:
            print(f"Creating empty {filename} file...")
            with open(filename, 'w', encoding='utf-8') as f:
                if filename.endswith('_images.txt'):
                    f.write("domain,original_url,recorded_at\n")
                elif filename.endswith('_list.txt'):
                    f.write("# Auto-generated file list\n")
            print(f"Created empty {filename} file.")
        else:
            print(f"Please create {filename} before building.")
            return False
    return True

def find_mitmproxy_binaries():
    """Find mitmproxy binaries in the system."""
    mitm_binaries = {}
    
    # 가능한 경로 목록
    possible_paths = []
    
    # 시스템 PATH에서 검색
    for path_dir in os.environ.get('PATH', '').split(os.pathsep):
        if path_dir and os.path.exists(path_dir):
            possible_paths.append(path_dir)
    
    # Python site-packages에서 검색
    try:
        site_packages = site.getsitepackages()
        for site_pkg in site_packages:
            if os.path.exists(site_pkg):
                # mitmproxy 바이너리가 있을 수 있는 경로 추가
                possible_paths.append(os.path.join(site_pkg, 'mitmproxy', 'tools'))
                possible_paths.append(os.path.join(site_pkg, 'bin'))
    except Exception as e:
        print(f"Warning: Could not check site-packages: {e}")
    
    # 사용자 홈 디렉토리의 Python 관련 경로 추가
    home = str(Path.home())
    possible_paths.extend([
        os.path.join(home, '.local', 'bin'),
        os.path.join(home, 'Library', 'Python', '3.9', 'bin'),
        os.path.join(home, 'Library', 'Python', '3.10', 'bin'),
        os.path.join(home, 'Library', 'Python', '3.11', 'bin'),
    ])
    
    # 바이너리 이름 (OS에 따라 다름)
    binary_names = ['mitmdump']
    if platform.system() == 'Windows':
        binary_names = ['mitmdump.exe']
    
    # 모든 가능한 경로에서 바이너리 검색
    for path_dir in possible_paths:
        for binary in binary_names:
            full_path = os.path.join(path_dir, binary)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                mitm_binaries[binary] = full_path
                print(f"Found {binary} at: {full_path}")
    
    return mitm_binaries

def main():
    print("=" * 60)
    print("이미지 프록시 패키지 빌드 스크립트")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    # 필요한 파일 확인
    required_files = [
        "woven-province-411903-b1b12d94b3ac.json",
        "cdn_file_list.txt",
        "smaller_original_images.txt"
    ]
    
    all_files_exist = True
    for file in required_files:
        if file.endswith('.json'):
            # JSON 파일은 빈 파일을 생성하지 않음
            if not ensure_file_exists(file, create_empty=False):
                all_files_exist = False
        else:
            # 기타 파일은 필요시 빈 파일 생성
            ensure_file_exists(file, create_empty=True)
    
    if not all_files_exist:
        print("필수 파일이 누락되었습니다. 빌드를 중단합니다.")
        return
    
    # 필요한 디렉토리 생성
    for directory in ["emission_logs", "carbon_logs"]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
    
    # mitmproxy 바이너리 찾기
    print("\nmitmproxy 바이너리 검색 중...")
    mitm_binaries = find_mitmproxy_binaries()
    
    if not mitm_binaries:
        print("경고: mitmproxy 바이너리를 찾을 수 없습니다.")
        print("사용자가 mitmproxy를 별도로 설치해야 할 수 있습니다.")
        proceed = input("계속 진행하시겠습니까? (y/n): ").lower().strip()
        if proceed != 'y':
            print("빌드를 중단합니다.")
            return
    
    # spec 파일이 이미 수정되어 있으므로 자동 업데이트를 건너뜁니다.
    print("이미 수정된 spec 파일을 사용합니다.")
    
    # PyInstaller 명령 실행
    print("\n빌드 시작...")
    try:
        # 이전 빌드 정리
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        
        # PyInstaller 실행
        result = subprocess.run(
            ["pyinstaller", "-y", "img_proxy.spec"],
            check=True,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("경고/오류:")
            print(result.stderr)
        
        # 빌드 성공 확인
        if os.path.exists("dist/img_proxy"):
            print("\n빌드 성공!")
            print(f"패키지 위치: {os.path.abspath('dist/img_proxy')}")
            
            # 추가 파일 복사
            for directory in ["emission_logs", "carbon_logs"]:
                dest_dir = os.path.join("dist/img_proxy", directory)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                    print(f"Created directory in package: {directory}")
            
            print("\n패키지 내용:")
            for root, dirs, files in os.walk("dist/img_proxy"):
                level = root.replace("dist/img_proxy", "").count(os.sep)
                indent = " " * 4 * level
                print(f"{indent}{os.path.basename(root)}/")
                sub_indent = " " * 4 * (level + 1)
                for file in files:
                    print(f"{sub_indent}{file}")
        else:
            print("\n빌드 실패: 패키지가 생성되지 않았습니다.")
    
    except subprocess.CalledProcessError as e:
        print(f"빌드 실패: {e}")
        print(e.stderr)
    except Exception as e:
        print(f"오류 발생: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n빌드가 사용자에 의해 중단되었습니다.")
        sys.exit(1)
