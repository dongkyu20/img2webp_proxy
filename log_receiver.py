# log_monitor_server.py (PC B에서 실행 - FastAPI 버전)
import datetime
from typing import Optional # Optional 필드를 위해 추가

from fastapi import FastAPI, HTTPException, status # FastAPI 관련 클래스 가져오기
from pydantic import BaseModel, Field # 데이터 유효성 검사를 위한 Pydantic 모델
from convert_n_upload import process_image

import uvicorn # FastAPI 서버 실행을 위해 필요

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "woven-province-411903-b1b12d94b3ac.json"

# 이 코드는 스크립트의 시작 부분에 추가하면 됩니다
# main() 함수 호출 전에 위치시키세요

# --- Pydantic 모델 정의 ---
# 요청 본문(JSON)의 구조를 정의하고 유효성을 검사합니다.
class LogEntry(BaseModel):
    level: Optional[str] = 'INFO' # 기본값 설정
    message: Optional[str] = ''
    origin_url: Optional[str] = ''
    domain: Optional[str] = ''
    original_filename: Optional[str] = ''
    filename_base: Optional[str] = ''
    original_path_query: Optional[str] = ''
    # timestamp가 없으면 현재 시간으로 동적 기본값 설정
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.datetime.now().isoformat())

# --- FastAPI 앱 생성 ---
app = FastAPI()

# --- API 엔드포인트 정의 ---
@app.post("/log") # POST 메서드의 /log 경로
async def receive_log(log_entry: LogEntry): # 요청 본문을 LogEntry 모델에 자동으로 바인딩
    """mitmproxy로부터 로그 메시지를 받아 콘솔에 출력합니다."""
    try:
        # Pydantic 모델 덕분에 데이터 유효성 검사 및 기본값 처리가 이미 완료됨
        # log_entry 객체의 속성으로 데이터에 접근

        # 중요: 여기서 콘솔에 로그를 출력합니다!
        print(f"[{log_entry.timestamp}] [{log_entry.level.upper()}] {log_entry.message} (Missed_URL: {log_entry.origin_url}) (Domain: {log_entry.domain})")
        print(f"\nprocess_image {log_entry.domain} {log_entry.origin_url}\n")
        process_image(log_entry.domain, log_entry.origin_url, "cdn.ecarbon.kr", 100, log_entry.filename_base, log_entry.original_path_query)

        # 성공 응답 반환 (FastAPI가 자동으로 JSON으로 변환)
        return {"status": "received"}

    except Exception as e:
        # 서버 내부 오류 로깅 (실제 운영 환경에서는 logging 모듈 사용 권장)
        print(f"[SERVER ERROR] Error processing log request: {e}")
        # FastAPI의 표준 오류 처리 방식 사용
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing log request: {str(e)}"
        )

# --- 서버 실행 ---
if __name__ == "__main__":
    # 실행할 호스트 및 포트 설정
    HOST = "0.0.0.0" # 모든 인터페이스에서 접속 허용
    PORT = 5000      # 요청받은 5000번 포트 사용

    print(f"Log monitoring server starting on http://{HOST}:{PORT}")
    print("Ensure firewall allows incoming connections on this port.")
    print("-----------------------------------------------------------")
    print("To run manually with auto-reload (for development):")
    print(f"uvicorn {__file__.split('/')[-1].replace('.py', '')}:app --host {HOST} --port {PORT} --reload")
    print("-----------------------------------------------------------")

    # Uvicorn 서버를 프로그램적으로 실행
    # host='0.0.0.0' 로 설정해야 다른 PC에서 접속 가능합니다.
    # PC B의 방화벽에서 이 포트에 대한 인바운드 연결을 허용해야 할 수 있습니다.
    uvicorn.run(app, host=HOST, port=PORT)