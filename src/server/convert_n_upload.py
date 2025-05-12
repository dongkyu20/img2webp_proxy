import os
import requests
from PIL import Image
from io import BytesIO
from google.cloud import storage
from google.cloud import firestore
import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "woven-province-411903-b1b12d94b3ac.json"


def download_image(image_url):
    """
    주어진 URL에서 이미지를 다운로드합니다.
    
    Args:
        image_url (str): 다운로드할 이미지의 URL
        
    Returns:
        BytesIO: 다운로드된 이미지의 바이트 데이터
    """
    try:
        response = requests.get("https://" + image_url, stream=True)
        response.raise_for_status()  # 에러 발생시 예외 발생
        return BytesIO(response.content)
    except requests.exceptions.RequestException as e:
        raise Exception(f"이미지 다운로드 중 오류 발생: {e}")

def convert_to_webp(image_data, quality=100, lossless=True):
    """
    이미지를 WebP 형식으로 변환하며 투명도를 유지합니다.

    Args:
        image_data (BytesIO): 원본 이미지 데이터
        quality (int): WebP 변환 품질 (0-100). lossless=True이면 무시될 수 있음.
        lossless (bool): 무손실 압축 사용 여부 (투명도 유지에 유리)

    Returns:
        BytesIO: WebP로 변환된 이미지 데이터 (투명도 유지)
    """
    try:
        img = Image.open(image_data)
        output = BytesIO()

        # 원본 이미지 모드를 유지하여 WebP로 저장
        # Pillow 라이브러리가 RGBA 또는 P 모드 등의 투명도를 WebP 저장 시 처리해줍니다.
        img.save(output, format="WEBP", quality=quality, lossless=lossless)
        output.seek(0)
        return output
    except Exception as e:
        raise Exception(f"WebP 변환 중 오류 발생 (투명도 유지 시도): {e}")

def upload_to_gcs(webp_data, bucket_name, domain, filename_base, original_path_query):
    """
    Google Cloud Storage에 WebP 이미지를 업로드합니다.
    
    Args:
        webp_data (BytesIO): WebP 이미지 데이터
        bucket_name (str): GCS 버킷 이름
        
    Returns:
        str: 업로드된 파일의 CDN URL
    """
    try:
        # 서비스 계정 인증 정보는 GOOGLE_APPLICATION_CREDENTIALS 환경 변수로 설정해야 합니다
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        blob = bucket.blob(f"{domain}/{original_path_query}{filename_base}.webp")
        blob.upload_from_file(webp_data, content_type='image/webp')
        
        # CDN URL 생성 (CDN이 구성된 경우)
        cdn_url = f"https://storage.cloud.google.com/{bucket_name}/{domain}/{original_path_query}{filename_base}.webp"
        
        return cdn_url
    except Exception as e:
        raise Exception(f"GCS 업로드 중 오류 발생: {e}")

def save_url_to_gcs(domain, original_url, bucket_name):
    """
    원본 이미지 크기가 WebP 이미지 크기보다 작은 경우, 원본 이미지 경로를 GCS 버킷의 텍스트 파일에 기록합니다.
    
    Args:
        domain (str): 이미지 도메인
        original_url (str): 원본 이미지 URL
        bucket_name (str): GCS 버킷 이름
    """
    try:
        # GCS 버킷에 텍스트 파일로 저장
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # 텍스트 파일 (루트 디렉토리에 위치)
        blob = bucket.blob('smaller_original_images.txt')
        
        # 현재 시간
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 파일이 이미 존재하는지 확인
        if blob.exists():
            content = blob.download_as_text()
            # URL이 이미 존재하는지 확인
            rows = content.split('\n')
            for row in rows[1:]:  # 헤더 제외
                if row and original_url in row:
                    print(f"URL이 이미 존재합니다, 중복 추가하지 않습니다: {original_url}")
                    return
            content += f"\n{domain},{original_url},{timestamp}"
        else:
            content = f"domain,original_url,recorded_at\n{domain},{original_url},{timestamp}"
        
        blob.upload_from_string(content, content_type='text/plain')
        
        print(f"원본 이미지 URL이 GCS에 기록되었습니다: {original_url}")
    except Exception as e:
        print(f"원본 이미지 URL 저장 중 오류 발생: {e}")


def process_image(domain, content_url, bucket_name, quality=100, filename_base=None, original_path_query=None):
    """
    이미지 URL에서 이미지를 다운로드하고, WebP로 변환한 후 GCS에 업로드합니다.
    
    Args:
        domain (str): 이미지가 로드된 도메인
        content_url (str): 이미지 URL
        bucket_name (str): GCS 버킷 이름
        quality (int): WebP 변환 품질 (0-100)
        destination_path (str, optional): GCS에 저장할 경로 및 파일명
        
    Returns:
        str: 업로드된 파일의 CDN URL
    """
    try:
        # 이미지 다운로드
        image_data = download_image(domain + content_url)
        
        # WebP로 변환
        webp_data = convert_to_webp(image_data, quality)

        # 원본 이미지 파일 크기 (바이트 단위)
        ori_size = len(image_data.getvalue())

        # WebP 이미지 파일 크기 (바이트 단위)
        webp_size = len(webp_data.getvalue())

        if ori_size > webp_size:
            # GCS에 업로드
            upload_to_gcs(webp_data, bucket_name, domain, filename_base, original_path_query)
        else:
            full_content_url = "https://" + domain + content_url
            save_url_to_gcs(domain, full_content_url, bucket_name)
            
        return
    except Exception as e:
        raise Exception(f"image processing failed: {e}")
