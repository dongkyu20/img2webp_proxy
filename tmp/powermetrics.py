import subprocess
import time
import os
import signal

# powermetrics 명령어 (필요에 따라 샘플러 등 수정)
command = [
    "sudo", "powermetrics",
    "--samplers", "cpu_power,gpu_power,smc",
    "-i", "2000", # 2초 간격
    "-o", "emission_logs/carbon_log.txt" # 결과를 파일에 저장
]

# powermetrics 프로세스 시작
print("Starting powermetrics...")
proc = subprocess.Popen(command)
print(f"powermetrics started with PID: {proc.pid}")
time.sleep(2) # powermetrics가 시작될 시간 확보

# =============================================
# 여기에 전력 소모를 측정할 Python 코드를 넣으세요
print("Running your Python code...")
start_time = time.time()
# 예시: 간단한 계산 작업
total = 0
for i in range(10**7):
    total += i
end_time = time.time()
print(f"Python code finished in {end_time - start_time:.2f} seconds.")
# =============================================

# powermetrics 프로세스 종료 (sudo 권한으로 실행했으므로 sudo pkill 사용)
print("Stopping powermetrics...")
try:
    # sudo pkill을 직접 실행하는 것이 더 안정적일 수 있습니다.
    # os.kill(proc.pid, signal.SIGINT) # SIGINT로 종료 시도 (sudo 권한 문제 가능)
    subprocess.run(["sudo", "pkill", "-f", "powermetrics"], check=True)
    print("powermetrics stopped.")
except Exception as e:
    print(f"Failed to stop powermetrics automatically: {e}")
    print(f"Please stop it manually using 'sudo pkill -f powermetrics'")

print("Power metrics saved to emission_logs/carbon_log.txt")

# 이제 power_metrics_output.txt 파일을 분석하여 전력 정보를 확인합니다.