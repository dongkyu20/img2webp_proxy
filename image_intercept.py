# -*- coding: utf-8 -*-
from mitmproxy import http
from mitmproxy import ctx
import re
import os
from urllib.parse import urlparse # URL 경로 분석에 필요

# --- 사용자 설정 ---
# 사용자의 CDN 기본 URL을 여기에 입력하세요.
# 예: "https://storage.cloud.google.com/cdn.ecarbon.kr"
# 중요: URL 끝에 슬래시(/)를 포함하지 않는 것이 좋습니다.
CDN_BASE_URL = "https://storage.cloud.google.com/cdn.ecarbon.kr"
# --- 사용자 설정 끝 ---

# 원본 이미지 확장자 매칭을 위한 정규 표현식 (대소문자 무시, 쿼리 파라미터 허용)
# .png, .jpg, .jpeg 확장자를 찾습니다.
ORIGINAL_IMAGE_EXT_REGEX = re.compile(r"\.(png|jpe?g)(\?.*)?$", re.IGNORECASE)

# CDN URL이 비어 있는지 확인
if not CDN_BASE_URL or CDN_BASE_URL == "https://your-cdn-domain.com":
    print("Warning: CDN_BASE_URL is not set in the script. Please configure it.")


class ImageFlattenWebpRedirector:
    """
    png/jpg/jpeg 이미지 요청 시, 원본 경로의 디렉토리는 무시하고
    파일명만 사용하여 CDN 루트의 해당 .webp 파일로 리다이렉트하는 mitmproxy 애드온.
    """
    def request(self, flow: http.HTTPFlow) -> None:
        """
        클라이언트의 모든 HTTP 요청이 서버로 전송되기 전에 호출됩니다.
        """
        # 1. 요청된 URL의 경로(path) 부분에서 원본 이미지 확장자를 확인합니다.
        match = ORIGINAL_IMAGE_EXT_REGEX.search(flow.request.path)
        if match:
            original_path_full = flow.request.path # 예: /images/uploads/cat.jpg?v=123

            # 2. URL을 파싱하여 쿼리 스트링 없는 순수 경로만 얻습니다.
            parsed_url = urlparse(original_path_full)
            original_path_no_query = parsed_url.path # 예: /images/uploads/cat.jpg
            # Query string (parsed_url.query)은 이 로직에서는 사용하지 않습니다.

            # 3. 순수 경로에서 디렉토리 부분을 제외하고 파일명만 추출합니다.
            original_filename = os.path.basename(original_path_no_query) # 예: cat.jpg

            # 4. 파일명에서 확장자를 분리합니다.
            filename_base, original_ext = os.path.splitext(original_filename)
            # filename_base = cat, original_ext = .jpg

            # 5. 새로운 파일명을 .webp 확장자로 구성합니다.
            new_filename = filename_base + ".webp" # 예: cat.webp

            # 6. 최종 CDN URL을 구성합니다. (CDN 베이스 + 새 파일명)
            # CDN_BASE_URL과 새 파일명 사이에 슬래시(/)가 하나만 있도록 처리합니다.
            if CDN_BASE_URL.endswith('/'):
                # CDN URL이 /로 끝나면 바로 파일명 붙임
                cdn_url = CDN_BASE_URL + new_filename
            else:
                # CDN URL이 /로 안 끝나면 / 추가 후 파일명 붙임
                cdn_url = CDN_BASE_URL + '/' + new_filename

            # 7. 리다이렉션 로그 출력
            ctx.log.info(
                f"[Image Flatten WEBP Redirect] Redirecting '{flow.request.pretty_url}' "
                f"to flattened WEBP '{cdn_url}'"
            )

            # 8. 브라우저에게 CDN의 루트에 있는 .webp 파일 URL로 리다이렉트하라는 응답 생성
            flow.response = http.Response.make(
                302,  # Status code: Found (Temporary Redirect)
                b"",  # Response body
                {
                    "Location": cdn_url, # 최종 CDN URL (.webp 파일명만 포함)
                    "Content-Type": "text/plain",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
            )

# mitmproxy가 애드온을 로드할 수 있도록 addons 리스트에 클래스 인스턴스를 추가합니다.
addons = [
    ImageFlattenWebpRedirector()
]