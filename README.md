# Google Solution Challenge 2025(eCarbon)

## Image Proxy Installation and Usage Guide

## Installation

### 1. Clone Repository and Set Up Virtual Environment
- Clone this repository: `git clone [repository-url]`
- Navigate to the project directory: `cd DomainModify_Proxy`
- Create a Python virtual environment: `python -m venv venv`
- Activate the virtual environment:
  - macOS/Linux: `source venv/bin/activate`
  - Windows: `venv\Scripts\activate`
- Install required libraries: `pip install -r requirements.txt`

### 2. Install mitmproxy
- Install mitmproxy in the virtual environment: `pip install mitmproxy`

### 3. Install mitmproxy Certificate
- Run the proxy GUI: `python src/client/proxy_gui.py`
- Start the proxy and visit http://mitm.it in your web browser
- Download and install the certificate appropriate for your operating system

#### OS-Specific Certificate Installation
- **macOS**: Double-click the downloaded certificate (.pem) to add it to Keychain Access, then set it to 'Always Trust'.
- **Linux**: Add the downloaded certificate to the system certificate store (methods vary by distribution).
- **Windows**: Double-click the downloaded certificate and select 'Install Certificate', choose 'Local Machine', and store it in 'Trusted Root Certification Authorities'.

## Running the Application

### Running the Proxy GUI
- With the virtual environment activated, run the following command:
  ```
  python src/client/proxy_gui.py
  ```
- Once the GUI starts, click the 'Start Proxy' button to activate the proxy.

## Important Notes
- The packaged version is currently not available, so you must run the application through the virtual environment.
- To use Google Cloud Storage features, a service account key file is required.

---

# 이미지 프록시 설치 및 사용 가이드

## 설치

### 1. 저장소 클론 및 가상환경 설정
- 이 저장소를 클론합니다: `git clone [repository-url]`
- 프로젝트 디렉토리로 이동합니다: `cd DomainModify_Proxy`
- Python 가상환경을 생성합니다: `python -m venv venv`
- 가상환경을 활성화합니다:
  - macOS/Linux: `source venv/bin/activate`
  - Windows: `venv\Scripts\activate`
- 필요한 라이브러리를 설치합니다: `pip install -r requirements.txt`

### 2. mitmproxy 설치
- 가상환경에 mitmproxy를 설치합니다: `pip install mitmproxy`

### 3. mitmproxy 인증서 설치
- 프록시 GUI를 실행합니다: `python src/client/proxy_gui.py`
- 프록시를 시작하고 웹 브라우저에서 http://mitm.it 에 접속합니다
- 운영체제에 맞는 인증서를 다운로드하고 설치합니다

#### 운영체제별 인증서 설치 방법
- **macOS**: 다운로드한 인증서(.pem)를 더블클릭하여 키체인 접근에 추가한 다음 '항상 신뢰'로 설정합니다.
- **Linux**: 다운로드한 인증서를 시스템 인증서 저장소에 추가합니다(배포판에 따라 방법이 다름).
- **Windows**: 다운로드한 인증서를 더블클릭하고 '로컬 컴퓨터'에 설치를 선택한 후 '신뢰할 수 있는 루트 인증 기관'에 저장합니다.

## 애플리케이션 실행

### 프록시 GUI 실행
- 가상환경이 활성화된 상태에서 다음 명령을 실행합니다:
  ```
  python src/client/proxy_gui.py
  ```
- GUI가 시작되면 '프록시 시작' 버튼을 클릭하여 프록시를 활성화합니다.

## 주의사항
- 현재 패키징 버전은 사용할 수 없으므로 반드시 가상환경을 통해 실행해야 합니다.
- Google Cloud Storage 기능을 사용하려면 서비스 계정 키 파일이 필요합니다.

## Troubleshooting

### Common Issues

1. **mitmproxy Execution Errors**
   - Error message: `Error logged during startup, exiting...`
   - Solution: Verify all required dependencies are installed. Try running `pip install -r requirements.txt` again.

2. **Google Cloud Storage Related Errors**
   - Error message: `No module named 'google.cloud'`
   - Solution: Run `pip install google-cloud-storage` to install the Google Cloud Storage library.

3. **Certificate Issues**
   - Symptom: Unable to access HTTPS websites
   - Solution: Download the certificate again from http://mitm.it and verify it's properly installed.

4. **Port Conflicts**
   - Error message: `[Port 8227 is already in use]`
   - Solution: Check if another program is using the port and terminate it if necessary. Alternatively, you can change the port number in the `set_proxy_addr.py` file.

### Checking Logs

Check the console output for troubleshooting. Detailed error messages will be displayed.

---

## 문제 해결

### 일반적인 문제

1. **mitmproxy 실행 오류**
   - 오류 메시지: `Error logged during startup, exiting...`
   - 해결 방법: 필요한 모든 종속성이 설치되어 있는지 확인하세요. `pip install -r requirements.txt`를 다시 실행해보세요.

2. **Google Cloud Storage 관련 오류**
   - 오류 메시지: `No module named 'google.cloud'`
   - 해결 방법: `pip install google-cloud-storage`를 실행하여 Google Cloud Storage 라이브러리를 설치하세요.

3. **인증서 관련 문제**
   - 증상: HTTPS 웹사이트에 접속할 수 없음
   - 해결 방법: http://mitm.it 에서 인증서를 다시 다운로드하고 올바르게 설치했는지 확인하세요.

4. **포트 충돌**
   - 오류 메시지: `[Port 8227 is already in use]`
   - 해결 방법: 다른 프로그램이 해당 포트를 사용 중인지 확인하고, 필요하다면 종료하세요. 또는 `set_proxy_addr.py` 파일에서 포트 번호를 변경할 수 있습니다.

### 로그 확인

문제 해결을 위해 콘솔 출력을 확인하세요. 자세한 오류 메시지가 표시됩니다.

## Important Notes

- When the program is terminated, proxy settings will be automatically restored to their original state.
- Carbon emission logs are stored in the server database.
- It is recommended to close all previously open browser windows before running the program.
- Some domains may not function correctly due to certificate issues.

---

## 중요 사항

- 프로그램을 종료하면 프록시 설정이 자동으로 원래대로 복원됩니다.
- 탄소 배출 로그는 서버 데이터베이스에 저장됩니다.
- 프로그램을 실행하기 전에 이전에 열려 있던 모든 브라우저 창을 닫는 것이 좋습니다.
- 일부 도메인은 인증서 문제로 인해 올바르게 작동하지 않을 수 있습니다.

## Troubleshooting

- **Certificate Error**: If the certificate is not installed correctly, run the `install_cert` program or download and install the certificate from http://mitm.it.
- **Proxy Connection Error**: Check if other proxy programs are running and terminate them.
- **File Path Error**: Ensure the necessary file (e.g., `cdn_file_list.txt`) is present in the directory where the program is executed.
- **502 Bad Gateway**: For domains encountering this error, it is recommended to close the program before accessing them.

---

## 문제 해결

- **인증서 오류**: 인증서가 올바르게 설치되지 않은 경우 `install_cert` 프로그램을 실행하거나 http://mitm.it 에서 인증서를 다운로드하여 설치합니다.
- **프록시 연결 오류**: 다른 프록시 프로그램이 실행 중인지 확인하고 종료합니다.
- **파일 경로 오류**: 프로그램을 실행한 디렉토리에서 필요한 파일(cdn_file_list.txt)이 있는지 확인합니다.
- **502 Bad Gateway**: 해당 에러가 발생하는 도메인에서는 프로그램을 종료한 후 접속하기를 권장합니다.

## Additional Information

- This program uses mitmproxy to detect image requests on web pages and serves PNG/JPEG images converted to WebP format.
- The application tracks carbon emissions when accessing web pages using the codecarbon library.
- All necessary data files are created automatically if they don't exist.
- It reduces data usage by utilizing WebP images stored in Google Cloud Storage.
- If you are the first to encounter a WebP image not yet stored in Google Cloud Storage, you enable its storage on the server, making it available for other users.

---

## 추가 정보

- 이 프로그램은 mitmproxy를 사용하여 웹 페이지의 이미지 요청을 감지하고 PNG/JPEG 이미지를 WebP 형식으로 변환하여 제공합니다.
- 이 애플리케이션은 codecarbon 라이브러리를 사용하여 웹 페이지 접속 시 탄소 배출량을 추적합니다.
- 필요한 모든 데이터 파일은 존재하지 않을 경우 자동으로 생성됩니다.
- Google Cloud Storage에 저장된 WebP 이미지를 활용하여 데이터 사용량을 줄입니다.
- 아직 Google Cloud Storage에 저장되지 않은 WebP 이미지를 처음 접하는 경우, 해당 이미지가 서버에 저장되어 다른 사용자들에게도 제공됩니다.
- 일부 도메인에서는 제대로 작동하지 않을 수 있습니다. 개발자들이 이러한 문제를 해결하기 위해 노력하고 있습니다.


# 이미지 프록시 설치 및 사용 설명서

## 설치 방법

### 1. 배포 패키지 다운로드 및 압축 해제
- 제공된 배포 패키지(zip 또는 압축 파일)를 다운로드합니다.
- 원하는 위치에 압축을 해제합니다.

### 2. mitmproxy 인증서 설치
- 배포 패키지에 포함된 `img_proxy`를 실행한 후 `install_cert` 프로그램을 실행합니다.
- 화면의 설명에 따라 인증서를 설치합니다.
- 프로그램 실행 후 웹 브라우저에서 http://mitm.it 에 접속하여 인증서를 직접 다운로드할 수도 있습니다.

#### 운영체제별 인증서 설치 방법
- **macOS**: 다운로드한 인증서(.pem)를 더블클릭하여 키체인에 추가하고 '항상 신뢰'로 설정
- **Linux**: 다운로드한 인증서를 시스템 인증서 저장소에 추가 (배포판에 따라 방법이 다름)
- **Windows**: 추가 예정, 미출시

## 사용 방법

1. 배포 패키지에서 `img_proxy` 실행 파일을 실행합니다.
   - macOS/Linux: 터미널에서 `./img_proxy` 실행
2. 프로그램이 자동으로 시스템 프록시 설정을 구성합니다.
3. 웹 브라우저에서 웹 페이지를 방문하면 이미지가 자동으로 WebP 형식으로 변환됩니다.
4. 프로그램을 종료하려면 콘솔 창에서 Ctrl+C를 누르거나 창을 닫으면 됩니다.

## 주의사항

- 프로그램을 종료하면 프록시 설정이 자동으로 원래대로 복원됩니다.
- 탄소 배출량 로그는 서버 데이터베이스에 저장됩니다.
- 실행 전에 이전에 열려있는 브라우저 창을 모두 닫는 것이 좋습니다.
- 몇몇 도메인은 인증서 문제로 인해 정상적으로 작동하지 않을 수 있습니다.

## 문제 해결

- **인증서 오류**: 인증서가 올바르게 설치되지 않은 경우 `install_cert` 프로그램을 실행하거나 http://mitm.it 에서 인증서를 다운로드하여 설치합니다.
- **프록시 연결 오류**: 다른 프록시 프로그램이 실행 중인지 확인하고 종료합니다.
- **파일 경로 오류**: 프로그램을 실행한 디렉토리에서 필요한 파일(cdn_file_list.txt)이 있는지 확인합니다.
- **502 Bad Gateway**: 해당 에러가 발생하는 도메인에서는 프로그램을 종료한 후 접속하기를 권장합니다.

## 추가 정보

- 이 프로그램은 mitmproxy를 이용하여 웹 페이지의 이미지 요청을 감지하고, PNG/JPEG 이미지를 WebP 형식으로 변환하여 제공합니다.
- 탄소 배출량 추적 기능이 포함되어 있어 웹 페이지 접속 시 탄소 배출량을 자동으로 기록합니다.
- Google Cloud Storage에 저장된 WebP 이미지를 사용하여 데이터 사용량을 절감합니다.
- Google Cloud Storage에 저장되어 있지 않은 WebP 이미지의 최초 발견자가 된다면 여러분은 서버를 통해 WebP 이미지를 저장할 수 있도록 하며, 그 이미지는 다른 사용자가 사용할 수 있습니다.
- 일부 도메인에서 정상작동 하지 않을 수 있습니다. 개발자가 해당 문제를 해결하기 위해 노력하는 중입니다.