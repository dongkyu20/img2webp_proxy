import os
import json
from google.cloud import storage
from google.api_core import exceptions # 예외 처리를 위해 임포트
from google.oauth2 import service_account # 서비스 계정 인증을 위해 임포트

os.environ["REQUESTS_CA_BUNDLE"] = "mitmproxy-ca-cert.pem"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "woven-province-411903-b1b12d94b3ac.json"

# 서비스 계정 키 파일 경로
KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "woven-province-411903-b1b12d94b3ac.json")


def list_blobs_in_bucket(bucket_name, output_file="cdn_file_list.txt", timeout=None):
    """Print the list of files in the specified Google Cloud Storage bucket and save it to a text file."""
    
    # 서비스 계정 자격 증명 명시적 로드
    credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
    
    # 명시적 자격 증명으로 클라이언트 초기화
    storage_client = storage.Client(credentials=credentials)
    storage_client._http.timeout = timeout if timeout else None

    try:
        # Get all blobs (files) in the bucket
        # list_blobs() returns an iterator
        blobs = storage_client.list_blobs(bucket_name)

        print(f"'{bucket_name}' bucket file list:")
        
        # Open file for writing
        with open(output_file, 'w', encoding='utf-8') as f:
            found_files = False
            for blob in blobs:
                blob_name = blob.name
                blob_size = blob.size  # File size (bytes)
                size_kb = blob_size / 1024  # KB unit conversion
                size_mb = size_kb / 1024  # MB unit conversion
                
                # Select appropriate size unit
                if size_mb >= 1:
                    size_display = f"{size_mb:.2f} MB"
                else:
                    size_display = f"{size_kb:.2f} KB"
                
                print(f"- {blob_name} (size: {size_display})") # Console output
                f.write(f"{blob_name}\t{blob_size}\n") # Save to file (tab separated)
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