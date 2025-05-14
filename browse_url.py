import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# 다운로드한 ChromeDriver 실행 파일의 전체 경로를 지정하세요.
# 예: '/path/to/your/chromedriver' 또는 'C:\\path\\to\\your\\chromedriver.exe'
# 시스템 PATH에 ChromeDriver 경로가 추가되어 있다면 경로를 지정하지 않아도 될 수 있습니다.
CHROME_DRIVER_PATH = '/Users/admin/Downloads/chromedriver-mac-arm64/chromedriver' # <--- 이 경로를 수정하세요!

urls = [
    "https://www.gla.ac.in",
    "https://www.pfw.edu",
    "https://www.pw.edu.pl",
    "https://www.uga.edu",
    "https://ictuniversity.edu.cm",
    "http://www.uic.edu",
    "https://uvce.ac.in",
    "https://jaipur.manipal.edu",
    "https://www.bucknell.edu",
    "https://www.thk.edu.tr",
    "https://www.giet.edu",
    "https://aaua.edu.ng",
    "https://www.ostimteknik.edu.tr",
    "http://www.ub.bw",
    "https://www.tu.edu.sa"
]

# 크롬 옵션 설정
chrome_options = Options()
# 캐시 비활성화 관련 옵션들
chrome_options.add_argument('--disable-application-cache')
chrome_options.add_argument('--disable-cache')
chrome_options.add_argument('--disk-cache-size=0')
chrome_options.add_argument('--media-cache-size=0')
# 필요에 따라 시크릿 모드(Incognito) 옵션을 추가할 수도 있습니다.
# chrome_options.add_argument('--incognito')

# ChromeDriver 서비스 설정
service = Service(executable_path=CHROME_DRIVER_PATH)

# WebDriver 인스턴스 생성 (크롬 브라우저 실행)
# Selenium 4 이상 방식
try:
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # URL 순차 접속
    for url in urls:
        print(f"{url} 접속 중 (캐시 비활성화)...")
        try:
            driver.get(url) # 현재 탭/창에서 URL 열기
            print("15초 대기...")
            time.sleep(15)
        except Exception as e:
            print(f"'{url}' 접속 중 오류 발생: {e}")
            print("15초 대기 후 다음 URL로 진행...")
            time.sleep(15) # 오류 발생 시에도 딜레이 유지

    print("모든 URL 접속 완료.")

except Exception as e:
    print(f"WebDriver 시작 중 오류 발생: {e}")
    print("ChromeDriver 경로가 정확한지, 버전이 Chrome 브라우저와 맞는지 확인하세요.")

finally:
    # WebDriver 종료 (브라우저 창 닫기)
    if 'driver' in locals() and driver:
        driver.quit()