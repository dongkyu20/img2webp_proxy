import os
from google.cloud import storage
from google.api_core import exceptions # 예외 처리를 위해 임포트

os.environ["REQUESTS_CA_BUNDLE"] = "mitmproxy-ca-cert.pem"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "woven-province-411903-b1b12d94b3ac.json"


def list_blobs_in_bucket(bucket_name, output_file="cdn_file_list.txt", timeout=None):
    """지정된 Google Cloud Storage 버킷의 파일 목록을 출력하고 텍스트 파일에 저장합니다."""
    
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
                print(f"- {blob_name}") # 콘솔에 출력
                f.write(f"{blob_name}\n") # 파일에 저장
                found_files = True

            if not found_files:
                print("  (버킷에 파일이 없습니다)")
                f.write("(버킷에 파일이 없습니다)\n")

    except exceptions.NotFound:
        print(f"오류: 버킷 '{bucket_name}'을(를) 찾을 수 없습니다.")
    except exceptions.Forbidden:
        print(f"오류: 버킷 '{bucket_name}'에 접근할 권한이 없습니다. IAM 권한을 확인하세요.")
    except Exception as e:
        print(f"알 수 없는 오류 발생: {e}")