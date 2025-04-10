# log_monitor_server.py (PC B에서 실행)
from flask import Flask, request, jsonify
import datetime
import logging
import requests
import os
import argparse
from urllib.parse import urlparse, urlunparse, unquote


# Flask 로깅 설정 (선택 사항: Flask 자체 로그 레벨 조정)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR) # Flask의 기본 요청 로그는 끄고 우리 로그만 보기 위함

app = Flask(__name__)

@app.route('/log', methods=['POST'])
def receive_log():
    """mitmproxy로부터 로그 메시지를 받아 콘솔에 출력합니다."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data received"}), 400

        log_level = data.get('level', 'INFO')
        message = data.get('message', '')
        origin_url = data.get('origin_url', '')
        domain = data.get('domain', '')
        timestamp = data.get('timestamp', datetime.datetime.now().isoformat()) # 타임스탬프가 없으면 지금 시간 사용

        # 중요: 여기서 콘솔에 로그를 출력합니다!
        print(f"[{timestamp}] [{log_level.upper()}] {message} (Missed_URL: {origin_url}) (Domain: {domain})")

        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"[SERVER ERROR] Error processing log request: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # 중요: host='0.0.0.0' 로 설정해야 다른 PC에서 접속 가능합니다.
    # 포트는 원하는 번호로 설정 (예: 5000)
    # PC B의 방화벽에서 이 포트에 대한 인바운드 연결을 허용해야 할 수 있습니다.
    print("Log monitoring server starting on port 5000...")
    print("Ensure firewall allows incoming connections on this port.")
    app.run(host='0.0.0.0', port=5000, debug=False) # debug=True 는 개발 시 유용