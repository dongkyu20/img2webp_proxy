import os
import requests
from PIL import Image
from io import BytesIO
from google.cloud import storage

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
        
        # GCS에 업로드
        cdn_url = upload_to_gcs(webp_data, bucket_name, domain, filename_base, original_path_query)
        
        return cdn_url
    except Exception as e:
        raise Exception(f"image processing failed: {e}")
