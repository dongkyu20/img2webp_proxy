#!/usr/bin/env python3
"""
baseline_emissions.py - 시스템 기본 탄소 배출량 측정 스크립트
"""

import os
import time
import datetime
import argparse
from codecarbon import EmissionsTracker

def measure_baseline_emissions(duration_minutes=5, output_dir="emission_logs", output_file="baseline_emissions.csv"):
    """
    지정된 시간 동안 시스템의 기본 탄소 배출량을 측정합니다.
    
    Args:
        duration_minutes (int): 측정 지속 시간(분)
        output_dir (str): 결과 저장 디렉토리
        output_file (str): 결과 저장 파일명
    """
    # 저장 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 시작 메시지 출력
    print(f"기본 탄소 배출량 측정을 시작합니다...")
    print(f"측정 시간: {duration_minutes}분")
    print(f"결과는 {os.path.join(output_dir, output_file)}에 저장됩니다.")
    
    # 고유 프로젝트명 생성 (타임스탬프 포함)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = f"baseline_measurement_{timestamp}"
    
    # 탄소 배출량 트래커 초기화
    tracker = EmissionsTracker(
        project_name=project_name,
        output_dir=output_dir,
        output_file=output_file,
        log_level="error"
    )
    
    # 측정 시작
    tracker.start()
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(minutes=duration_minutes)
    
    try:
        print(f"측정 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"측정 종료 예정: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("측정 중... (Ctrl+C를 누르면 중단됩니다)")
        
        # 주어진 시간 동안 대기 (측정 진행)
        elapsed_minutes = 0
        while elapsed_minutes < duration_minutes:
            time.sleep(60)  # 1분마다 상태 업데이트
            elapsed_minutes += 1
            remaining = duration_minutes - elapsed_minutes
            print(f"경과 시간: {elapsed_minutes}분 (남은 시간: {remaining}분)")
        
        # 측정 종료
        emissions_data = tracker.stop()
        actual_end_time = datetime.datetime.now()
        
        print("\n측정이 완료되었습니다!")
        print(f"실제 측정 종료: {actual_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"총 측정 시간: {(actual_end_time - start_time).total_seconds() / 60:.2f}분")
        
        # 결과 요약 출력
        print("\n=== 측정 결과 요약 ===")
        print(f"총 탄소 배출량: {emissions_data:.8f} kg CO2eq")
        print(f"시간당 배출량: {emissions_data * 60 / duration_minutes:.8f} kg CO2eq/시간")
        print(f"상세 결과는 {os.path.join(output_dir, output_file)}에 저장되었습니다.")
        
    except KeyboardInterrupt:
        # 사용자가 Ctrl+C로 중단한 경우
        print("\n사용자에 의해 측정이 중단되었습니다.")
        actual_end_time = datetime.datetime.now()
        actual_duration = (actual_end_time - start_time).total_seconds() / 60
        
        if actual_duration > 0:
            emissions_data = tracker.stop()
            print(f"부분 측정 시간: {actual_duration:.2f}분")
            print(f"부분 측정 탄소 배출량: {emissions_data:.8f} kg CO2eq")
            print(f"상세 결과는 {os.path.join(output_dir, output_file)}에 저장되었습니다.")
        else:
            tracker.stop()
            print("측정 시간이 너무 짧아 유효한 결과가 없습니다.")
    
    except Exception as e:
        print(f"\n오류 발생: {e}")
        tracker.stop()

if __name__ == "__main__":
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description="기본 시스템 탄소 배출량 측정 도구")
    parser.add_argument(
        "-d", "--duration", 
        type=int, 
        default=5, 
        help="측정 지속 시간(분) (기본값: 5분)"
    )
    parser.add_argument(
        "-o", "--output-dir", 
        type=str, 
        default="emission_logs", 
        help="결과 저장 디렉토리 (기본값: emission_logs)"
    )
    parser.add_argument(
        "-f", "--output-file", 
        type=str, 
        default="baseline_emissions.csv", 
        help="결과 저장 파일명 (기본값: baseline_emissions.csv)"
    )
    
    args = parser.parse_args()
    
    # 측정 실행
    measure_baseline_emissions(
        duration_minutes=args.duration,
        output_dir=args.output_dir,
        output_file=args.output_file
    )