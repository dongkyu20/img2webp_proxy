import os
from google.cloud import storage
from google.api_core import exceptions # 예외 처리를 위해 임포트

os.environ["REQUESTS_CA_BUNDLE"] = "mitmproxy-ca-cert.pem"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "woven-province-411903-b1b12d94b3ac.json"


def list_blobs_in_bucket(bucket_name, output_file="cdn_file_list.txt", timeout=None):
    """지정된 Google Cloud Storage 버킷의 파일 목록과 각 파일의 용량을 출력하고 텍스트 파일에 저장합니다."""
    
    # 클라이언트 초기화 - timeout 설정 추가
    storage_client = storage.Client()
    # 클라이언트 타임아웃 설정
    storage_client._http.timeout = timeout if timeout else None

    try:
        # 버킷 내의 모든 blob(파일) 목록 가져오기
        # list_blobs()는 iterator를 반환합니다.
        blobs = storage_client.list_blobs(bucket_name)

        print(f"'{bucket_name}' 버킷의 파일 목록:")
        
        # 파일에 쓰기 위해 파일 열기
        with open(output_file, 'w', encoding='utf-8') as f:
            found_files = False
            for blob in blobs:
                blob_name = blob.name
                blob_size = blob.size  # 파일 크기(bytes)
                size_kb = blob_size / 1024  # KB 단위 변환
                size_mb = size_kb / 1024  # MB 단위 변환
                
                # 적절한 크기 단위 선택
                if size_mb >= 1:
                    size_display = f"{size_mb:.2f} MB"
                else:
                    size_display = f"{size_kb:.2f} KB"
                
                print(f"- {blob_name} (크기: {size_display})") # 콘솔에 출력
                f.write(f"{blob_name}\t{blob_size}\n") # 파일에 저장 (탭으로 구분)
                found_files = True

            if not found_files:
                print("  (file not found in bucket)")
                f.write("(file not found in bucket)\n")

    except exceptions.NotFound:
        print(f"Error: Bucket '{bucket_name}' not found.")
    except exceptions.Forbidden:
        print(f"Error: Access to bucket '{bucket_name}' forbidden. Check IAM permissions.")
    except Exception as e:
        print(f"Unknown error: {e}")