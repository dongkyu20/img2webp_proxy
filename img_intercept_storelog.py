# -*- coding: utf-8 -*-
from mitmproxy import http
from mitmproxy import ctx
import re
import os
from urllib.parse import urlparse
import requests # 외부 HTTP 요청을 위한 라이브러리
import time
import json # JSON 데이터를 만들기 위해 추가
import datetime # 타임스탬프를 위해 추가

# --- 사용자 설정 ---
CDN_BASE_URL = "https://storage.cloud.google.com/cdn.ecarbon.kr" # 실제 CDN 주소로 변경
CHECK_TIMEOUT_SECONDS = 1 # CDN 확인 요청 타임아웃 (초)

# --- 원격 로깅 설정 ---
ENABLE_REMOTE_LOGGING = True # True로 설정하면 원격 로깅 활성화
# 중요: 아래 IP 주소를 PC B의 실제 IP 주소로 변경하세요!
REMOTE_LOG_SERVER_URL = "http://127.0.0.1:5000/log"
REMOTE_LOG_TIMEOUT_SECONDS = 2 # 원격 로깅 요청 타임아웃
# --- 원격 로깅 설정 끝 ---

# --- 사용자 설정 끝 ---

ORIGINAL_IMAGE_EXT_REGEX = re.compile(r"\.(png|jpe?g)(\?.*)?$", re.IGNORECASE)
checked_missing_webp_urls = set()

if not CDN_BASE_URL or CDN_BASE_URL == "https://your-cdn-domain.com":
    print("Warning: CDN_BASE_URL is not set. Please configure it.")

# --- 원격 로깅 함수 ---
def send_log_to_remote(level, message, original_path_full, domain):
    """지정된 서버로 로그 메시지를 POST 요청으로 전송합니다."""
    if not ENABLE_REMOTE_LOGGING:
        return

    try:
        payload = {
            "level": level,
            "message": message,
            "orgin_url": original_path_full,
            "domain": domain,
            "timestamp": datetime.datetime.now().isoformat() # 현재 시간 추가
        }
        headers = {'Content-Type': 'application/json'}
        # 이 요청은 비동기가 아니므로, 원격 로깅이 느리면 전체 프록시 성능에 영향을 줄 수 있음
        response = requests.post(
            REMOTE_LOG_SERVER_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=REMOTE_LOG_TIMEOUT_SECONDS
        )
        # 원격 로깅 실패 시 로컬에 에러 로그 남기기 (선택 사항)
        if response.status_code != 200:
            ctx.log.error(f"[Remote Logging Error] Failed to send log. Server responded with {response.status_code}")
    except requests.exceptions.RequestException as e:
        # 원격 로깅 실패 시 로컬에 에러 로그 남기기
        ctx.log.error(f"[Remote Logging Error] Failed to send log to {REMOTE_LOG_SERVER_URL}: {e}")
    except Exception as e:
        ctx.log.error(f"[Remote Logging Error] Unexpected error: {e}")


class CheckAndLogMissingWebp:
    def request(self, flow: http.HTTPFlow) -> None:
        match = ORIGINAL_IMAGE_EXT_REGEX.search(flow.request.path)
        if match:
            domain = flow.request.pretty_host
            original_path_full = flow.request.path
            parsed_url = urlparse(original_path_full)
            original_path_no_query = parsed_url.path
            original_filename = os.path.basename(original_path_no_query)
            filename_base, _ = os.path.splitext(original_filename)
            webp_filename = filename_base + ".webp"

            if CDN_BASE_URL.endswith('/'):
                cdn_webp_url = CDN_BASE_URL + webp_filename
            else:
                cdn_webp_url = CDN_BASE_URL + '/' + webp_filename

            if cdn_webp_url in checked_missing_webp_urls:
                return

            try:
                start_time = time.time()
                response = requests.head(cdn_webp_url, timeout=CHECK_TIMEOUT_SECONDS, allow_redirects=False)
                check_duration = time.time() - start_time

                if response.status_code == 200:
                    # ctx.log.info(...) # INFO 로그는 원격으로 보낼 필요 없을 수 있음
                    flow.response = http.Response.make(
                        302, b"", {"Location": cdn_webp_url, "Content-Type": "text/plain"}
                    )
                else:
                    log_message = (
                        f"[Missing WEBP] Not found ({response.status_code}) at {cdn_webp_url} "
                        f"(Original: {original_path_full}) (Check took {check_duration:.3f}s)"
                    )
                    # 로컬 로그 출력
                    ctx.log.warn(log_message)
                    # 원격 서버로 로그 전송
                    send_log_to_remote("WARN", log_message, original_path_full, domain)

                    checked_missing_webp_urls.add(cdn_webp_url)

            except requests.exceptions.Timeout:
                log_message = f"[CDN Check Error] Timeout checking for {cdn_webp_url}"
                # 로컬 로그 출력
                ctx.log.error(log_message)
                # 원격 서버로 로그 전송
                send_log_to_remote("ERROR", log_message, original_path_full, domain)
            except requests.exceptions.RequestException as e:
                log_message = f"[CDN Check Error] Failed to check {cdn_webp_url}: {e}"
                # 로컬 로그 출력
                ctx.log.error(log_message)
                # 원격 서버로 로그 전송
                send_log_to_remote("ERROR", log_message, original_path_full, domain)

addons = [
    CheckAndLogMissingWebp()
]