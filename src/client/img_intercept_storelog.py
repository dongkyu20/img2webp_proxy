# -*- coding: utf-8 -*-
from mitmproxy import http
from mitmproxy import ctx
import re
import os
from urllib.parse import urlparse
import requests # 외부 HTTP 요청을 위한 라이브러리
import json # JSON 데이터를 만들기 위해 추가
import datetime # 타임스탬프를 위해 추가
import threading
import time
from file_exists import list_blobs_in_bucket
from google.cloud import storage

os.environ["REQUESTS_CA_BUNDLE"] = "mitmproxy-ca-cert.pem"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "woven-province-411903-b1b12d94b3ac.json"

os.environ["HTTP_PROXY"] = "http://127.0.0.1:8227"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:8227"


# --- 사용자 설정 ---
CDN_BASE_URL = "https://storage.cloud.google.com/cdn.ecarbon.kr" # 실제 CDN 주소로 변경

# --- 원격 로깅 설정 ---
ENABLE_REMOTE_LOGGING = True # True로 설정하면 원격 로깅 활성화
# 중요: 아래 IP 주소를 PC B의 실제 IP 주소로 변경하세요!
REMOTE_LOG_SERVER_URL = "http://211.253.31.134:5000/log"
REMOTE_LOG_TIMEOUT_SECONDS = 0.15 # 원격 로깅 요청 타임아웃
# --- 원격 로깅 설정 끝 ---

# --- 사용자 설정 끝 ---

ORIGINAL_IMAGE_EXT_REGEX = re.compile(r"\.(png|jpe?g)(\?.*)?$|[_=](png|jpe?g)($|\?|&)|atchFileId=.*_(png|jpe?g)($|\?|&)", re.IGNORECASE)

# GCS 버킷 이름
BUCKET_NAME = "cdn.ecarbon.kr"
# 파일 목록 업데이트 주기 (초)
UPDATE_INTERVAL = 1800  # 30분 = 1800초
# 작은 이미지 목록 파일 이름
SMALLER_IMAGES_FILENAME = "smaller_original_images.txt"
# 작은 이미지 목록 로컬 파일 경로
SMALLER_IMAGES_LOCAL_PATH = "smaller_original_images.txt"

## 예외처리 리스트
BYPASS_DOMAINS = [
    "donga.ac.kr",
    "bufs.ac.kr",
    "www.ahnlab.com"
]

# CDN 파일 목록을 주기적으로 업데이트하는 함수
def update_cdn_file_list_periodically():
    """1시간마다 GCS 버킷의 파일 목록을 갱신합니다."""
    while True:
        try:
            ctx.log.info(f"[CDN File List] 파일 목록 업데이트 시작: {datetime.datetime.now().isoformat()}")
            list_blobs_in_bucket(BUCKET_NAME)
            ctx.log.info(f"[CDN File List] 파일 목록 업데이트 완료: {datetime.datetime.now().isoformat()}")
        except Exception as e:
            ctx.log.error(f"[CDN File List] 파일 목록 업데이트 중 오류 발생: {e}")
        
        # 지정된 시간(30분) 동안 대기
        time.sleep(UPDATE_INTERVAL)

# GCS 버킷에서 smaller_original_images.txt 파일을 다운로드하는 함수
def download_smaller_images_list(bucket_name, timeout=None):
    """GCS 버킷에서 원본 크기가 작은 이미지 목록(smaller_original_images.txt)을 다운로드합니다."""
    try:
        # 클라이언트 초기화
        storage_client = storage.Client()
        # 클라이언트 타임아웃 설정
        storage_client._http.timeout = timeout if timeout else None
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(SMALLER_IMAGES_FILENAME)
        
        # 파일이 존재하는지 확인
        if blob.exists():
            # 파일 다운로드
            blob.download_to_filename(SMALLER_IMAGES_LOCAL_PATH)
            ctx.log.info(f"[Smaller Images] {SMALLER_IMAGES_FILENAME} 파일 다운로드 완료")
            return True
        else:
            ctx.log.warn(f"[Smaller Images] {SMALLER_IMAGES_FILENAME} 파일이 버킷에 존재하지 않습니다")
            # 로컬에 빈 파일 생성
            with open(SMALLER_IMAGES_LOCAL_PATH, 'w', encoding='utf-8') as f:
                f.write("domain,original_url,recorded_at\n")
            return False
    except Exception as e:
        ctx.log.error(f"[Smaller Images] 파일 다운로드 중 오류 발생: {e}")
        return False

# 작은 이미지 목록 주기적으로 업데이트하는 함수
def update_smaller_images_list_periodically():
    """주기적으로 GCS 버킷에서 원본 크기가 작은 이미지 목록을 업데이트합니다."""
    while True:
        try:
            ctx.log.info(f"[Smaller Images] 목록 업데이트 시작: {datetime.datetime.now().isoformat()}")
            download_smaller_images_list(BUCKET_NAME)
            ctx.log.info(f"[Smaller Images] 목록 업데이트 완료: {datetime.datetime.now().isoformat()}")
        except Exception as e:
            ctx.log.error(f"[Smaller Images] 목록 업데이트 중 오류 발생: {e}")
        
        # 지정된 시간 동안 대기
        time.sleep(UPDATE_INTERVAL)

# 프로그램 시작시 최초 1회 파일 목록 업데이트 - 백그라운드 스레드로 실행하여 블로킹 방지
def init_cdn_file_list():
    ctx.log.info("[CDN File List] 초기 파일 목록 생성 중...")
    try:
        list_blobs_in_bucket(BUCKET_NAME, timeout=15)
        ctx.log.info("[CDN File List] 초기 파일 목록 생성 완료")
        
        # 작은 이미지 목록 초기 다운로드
        download_smaller_images_list(BUCKET_NAME, timeout=15)
    except Exception as e:
        ctx.log.error(f"[CDN File List] 초기 파일 목록 생성 중 오류 발생: {e}")

# 초기화와 주기적 업데이트를 모두 별도 스레드로 실행
init_thread = threading.Thread(target=init_cdn_file_list, daemon=True)
init_thread.start()
ctx.log.info("[CDN File List] 초기 파일 목록 생성 스레드 시작됨")

# 주기적 업데이트 스레드 시작
updater_thread = threading.Thread(target=update_cdn_file_list_periodically, daemon=True)
updater_thread.start()
ctx.log.info("[CDN File List] 주기적 업데이트 스레드 시작됨")

# 작은 이미지 목록 주기적 업데이트 스레드 시작
smaller_images_thread = threading.Thread(target=update_smaller_images_list_periodically, daemon=True)
smaller_images_thread.start()
ctx.log.info("[Smaller Images] 주기적 업데이트 스레드 시작됨")

# 파일에서 URL을 찾는 함수
def search_path(file_path, Target_URL):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, 1):
                line = line.strip()  # 줄 끝의 공백과 줄바꿈 문자 제거
                if Target_URL in line:
                    return True
            # 모든 줄을 검사했지만 찾지 못한 경우
            return False
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return False
    except Exception as e:
        print(f"파일 읽기 중 오류가 발생했습니다: {e}")
        return False

# 원본 이미지가 '작은 이미지 목록'에 있는지 확인하는 함수
def is_smaller_original_image(original_url):
    """원본 이미지 URL이 'smaller_original_images.txt'에 있는지 확인합니다."""
    try:
        with open(SMALLER_IMAGES_LOCAL_PATH, 'r', encoding='utf-8') as file:
            # 첫 줄(헤더)은 건너뛰기
            next(file, None)
            
            for line in file:
                if line.strip() and original_url in line:
                    return True
        return False
    except FileNotFoundError:
        ctx.log.warn(f"[Smaller Images] 파일을 찾을 수 없습니다: {SMALLER_IMAGES_LOCAL_PATH}")
        return False
    except Exception as e:
        ctx.log.error(f"[Smaller Images] 파일 읽기 중 오류 발생: {e}")
        return False




# --- 원격 로깅 함수 ---
def send_log_to_remote(level, message, original_path_full, domain, original_filename, filename_base, original_path_query):
    """지정된 서버로 로그 메시지를 POST 요청으로 전송합니다."""
    if not ENABLE_REMOTE_LOGGING:
        return
    try:
        payload = {
            "level": level,
            "message": message,
            "origin_url": original_path_full,
            "domain": domain,
            "original_filename": original_filename,
            "filename_base": filename_base,
            "original_path_query": original_path_query,
            "timestamp": datetime.datetime.now().isoformat() # 현재 시간 추가
        }
        headers = {'Content-Type': 'application/json'}

        # 중요: 프록시를 사용하지 않도록 명시적으로 설정
        proxies = {
          "http": None,
          "https": None,
        }

        # ctx.log.info(f"Attempting to send log DIRECTLY to {REMOTE_LOG_SERVER_URL}") # 디버깅 로그 추가 (선택사항)

        response = requests.post(
            REMOTE_LOG_SERVER_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=REMOTE_LOG_TIMEOUT_SECONDS,
            proxies=proxies # <-- 이 부분을 추가하세요!
        )

        if response.status_code != 200:
            ctx.log.error(f"[Remote Logging Error] Failed to send log. Server responded with {response.status_code}")
    except requests.exceptions.RequestException as e:
        # 에러 로그 개선: 프록시 정보가 포함될 수 있도록 전체 에러 출력
        ctx.log.error(f"[Remote Logging Error] Failed to send log to {REMOTE_LOG_SERVER_URL}: {e}")
    except Exception as e:
        ctx.log.error(f"[Remote Logging Error] Unexpected error during remote logging: {e}")



class CheckAndLogMissingWebp:
    ctx.options.ignore_hosts = BYPASS_DOMAINS
    def request(self, flow: http.HTTPFlow) -> None:    
        match = ORIGINAL_IMAGE_EXT_REGEX.search(flow.request.path)
        if match:
            domain = flow.request.pretty_host
            original_path_full = flow.request.path # 원본 URL
            parsed_url = urlparse(original_path_full)
            original_path_no_query = parsed_url.path
            original_path_query = parsed_url.query
            original_filename = os.path.basename(original_path_no_query)
            filename_base, _ = os.path.splitext(original_filename)
            webp_filename = original_path_query + filename_base + ".webp"
            webp_path = f"{domain}/{webp_filename}"

            # 경로 규칙 : CDN_BASE_URL / 도메인 주소 / 원본 경로의 쿼리문  + 원본 파일명.webp
            if CDN_BASE_URL.endswith('/'):
                cdn_webp_url = CDN_BASE_URL + domain + '/' + webp_filename
            else:
                cdn_webp_url = CDN_BASE_URL + '/' + domain + '/' + webp_filename

            try:
                # 원본 이미지가 '작은 이미지 목록'에 있는지 확인
                if is_smaller_original_image(original_path_full):
                    print(f"[Smaller Original] 원본 이미지가 '작은 이미지 목록'에 있습니다: {original_path_full}")
                    # # 작은 이미지 목록에 있으면 원본 이미지 사용
                    # flow.response = http.Response.make(
                    #     302,  # Status code: Found (Temporary Redirect)
                    #     b"",  # Response body
                    #     {
                    #     "Location": original_path_full, # 원본 이미지 URL 사용
                    #     "Content-Type": "text/plain",
                    #     "Cache-Control": "public, max-age=3600",
                    #     }
                    # )
                elif search_path("cdn_file_list.txt", webp_path):
                    print(f"\n\n{cdn_webp_url} is in list!\n\n")
                    flow.response = http.Response.make(
                        302,  # Status code: Found (Temporary Redirect)
                        b"",  # Response body
                        {
                        "Location": cdn_webp_url, # 최종 CDN URL (.webp 파일명만 포함)
                        "Content-Type": "text/plain",
                        "Cache-Control": "public, max-age=3600",
                        # "Pragma": "no-cache",
                        # "Expires": "0",
                        }
                    )
                    log_message = (
                        f"[Found WEBP] Found at {cdn_webp_url} "
                        f"(Original: {original_path_full})"
                    )
                    send_log_to_remote("SUCCESS", log_message, original_path_full, domain, original_filename, filename_base, original_path_query)
                else:
                    log_message = (
                        f"[Missing WEBP] Not found at {cdn_webp_url} "
                        f"(Original: {original_path_full})"
                    )
                    # 로컬 로그 출력
                    ctx.log.warn(log_message)
                    # 원격 서버로 로그 전송
                    send_log_to_remote("WARN", log_message, original_path_full, domain, original_filename, filename_base, original_path_query)
            except Exception as e:
                log_message = (
                    f"catch error {e}"
                    f"(Original: {original_path_full})"
                    f"(cdn_webp_url: {cdn_webp_url})"
                )
                # 로컬 로그 출력
                ctx.log.error(log_message)
                # 원격 서버로 로그 전송
                send_log_to_remote("ERROR", log_message, original_path_full, domain, original_filename, filename_base, original_path_query)

addons = [
    CheckAndLogMissingWebp()
]