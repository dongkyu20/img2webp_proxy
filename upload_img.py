from google.cloud import storage
import os

# --- 설정 ---
# 서비스 계정 키 파일 경로 설정 (환경 변수 GOOGLE_APPLICATION_CREDENTIALS 설정 권장)
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/your/keyfile.json'
GCS_BUCKET_NAME = 'cdn.ecarbon.kr'          # 실제 버킷 이름으로 변경
LOCAL_FILE_PATH = 'me_go_kr_webp/'       # 업로드할 로컬 이미지 파일 경로
GCS_BLOB_NAME = 'images/uploaded_image.jpg'       # GCS 버킷 내 저장될 경로 및 파일명
# -----------

# 로컬 파일 존재 확인
if not os.path.exists(LOCAL_FILE_PATH):
    print(f"오류: 파일 '{LOCAL_FILE_PATH}'을(를) 찾을 수 없습니다.")
else:
    try:
        # 스토리지 클라이언트 초기화 (자동으로 인증 정보 찾음)
        storage_client = storage.Client()

        # 버킷 가져오기
        bucket = storage_client.bucket(GCS_BUCKET_NAME)

        # Blob (객체) 생성
        blob = bucket.blob(GCS_BLOB_NAME)

        # 파일 업로드
        blob.upload_from_filename(
            LOCAL_FILE_PATH,
            content_type='image/jpeg' # 이미지 타입에 맞게 설정 (예: image/png)
        )

        print(f"'{LOCAL_FILE_PATH}' 파일을 '{GCS_BUCKET_NAME}/{GCS_BLOB_NAME}'(으)로 성공적으로 업로드했습니다.")

        # 업로드된 객체의 공개 URL (버킷/객체가 공개 상태일 때)
        # print(f"GCS 공개 URL: {blob.public_url}") # 공개 설정 필요
        # Cloud CDN URL은 별도로 확인해야 합니다.

    except Exception as e:
        print(f"파일 업로드 중 오류 발생: {e}")
    except FileNotFoundError:
         print(f"오류: 로컬 파일 '{LOCAL_FILE_PATH}'을(를) 찾을 수 없습니다.")

# 필요한 라이브러리 설치: pip install google-cloud-storage