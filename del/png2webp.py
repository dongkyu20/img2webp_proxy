import os
from PIL import Image
from pathlib import Path

def convert_to_webp(input_dir='me_go_kr', output_dir='me_go_kr_webp', quality=90):
    """
    PNG, JPG, JPEG 파일들을 WebP로 변환하여 별도의 출력 디렉토리에 저장합니다.
    투명도가 있는 이미지의 경우 투명도를 유지합니다.
    
    Args:
        input_dir (str): 이미지 파일이 있는 입력 디렉토리 경로
        output_dir (str): WebP 파일을 저장할 출력 디렉토리 경로
        quality (int): WebP 변환 품질 (0-100)
    """
    # 경로를 Path 객체로 변환
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # 성공 및 실패 카운터 초기화
    success_count = 0
    failed_count = 0
    
    # 파일 형식별 카운터
    format_counts = {
        'png': 0,
        'jpg': 0,
        'jpeg': 0
    }
    
    # 입력 디렉토리 존재 확인
    if not input_path.exists():
        print(f"오류: 입력 디렉토리를 찾을 수 없습니다: {input_path}")
        return
    
    # 출력 디렉토리 생성
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 지원하는 이미지 확장자들
    extensions = ['*.png', '*.jpg', '*.jpeg']
    
    # 각 확장자별로 파일 검색 및 변환
    for ext in extensions:
        for img_file in input_path.glob(ext):
            try:
                # 이미지 열기
                with Image.open(img_file) as img:
                    # 출력 파일 경로 생성
                    output_file = output_path / f"{img_file.stem}.webp"
                    
                    # 원본 이미지의 모드를 유지
                    if img.mode in ('RGBA', 'LA'):
                        # 알파 채널이 있는 경우 lossless로 저장
                        img.save(output_file, 'WEBP', quality=quality, lossless=True)
                    else:
                        # 알파 채널이 없는 경우 일반적인 압축 사용
                        img.save(output_file, 'WEBP', quality=quality)
                    
                    print(f"변환 성공: {img_file.name} -> {output_file.name}")
                    success_count += 1
                    
                    # 형식별 카운터 증가
                    format_counts[img_file.suffix[1:].lower()] += 1
                    
            except Exception as e:
                print(f"변환 실패: {img_file.name}")
                print(f"오류 메시지: {str(e)}")
                failed_count += 1
    
    # 결과 보고
    print("\n변환 완료 보고서:")
    print(f"성공: {success_count}개 파일")
    print(f"실패: {failed_count}개 파일")
    print(f"총 처리된 파일: {success_count + failed_count}개")
    print("\n형식별 변환 통계:")
    print(f"PNG 파일: {format_counts['png']}개")
    print(f"JPG 파일: {format_counts['jpg']}개")
    print(f"JPEG 파일: {format_counts['jpeg']}개")

if __name__ == "__main__":
    # 기본 디렉토리 설정으로 실행
    convert_to_webp()