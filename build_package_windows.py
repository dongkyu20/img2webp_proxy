#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Windows용 이미지 프록시 빌드 스크립트
PyInstaller를 사용하여 Windows 실행 파일을 생성합니다.
"""

import os
import subprocess
import shutil
import sys

def main():
    """
    Windows용 이미지 프록시 패키지를 빌드합니다.
    """
    try:
        print("Windows용 이미지 프록시 패키지 빌드를 시작합니다...")
        
        # 기존 빌드 제거
        if os.path.exists("build"):
            print("기존 build 디렉토리 제거 중...")
            shutil.rmtree("build")
        
        if os.path.exists("dist"):
            print("기존 dist 디렉토리 제거 중...")
            shutil.rmtree("dist")
        
        # PyInstaller로 빌드 실행
        print("\nPyInstaller로 패키지 빌드 중...")
        subprocess.run(["pyinstaller", "-y", "img_proxy_window.spec"], check=True)
        
        # 빌드 결과 확인
        if os.path.exists("dist/img_proxy.exe"):
            print("\n빌드 성공: 패키지가 생성되었습니다.")
            
            # 필요한 디렉토리 생성
            directories = ["emission_logs", "logs"]
            for directory in directories:
                dest_dir = os.path.join("dist/img_proxy.exe", directory)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                    print(f"Created directory in package: {directory}")
            
            print("\n패키지 내용:")
            for root, dirs, files in os.walk("dist/img_proxy.exe"):
                level = root.replace("dist/img_proxy.exe", "").count(os.sep)
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

if __name__ == "__main__":
    main()
