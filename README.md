# Image Proxy Installation and Usage Guide

## Installation

### 1. Download and Unzip the Distribution Package
- Download the provided distribution package (zip or compressed file).
- Unzip it to your desired location.

### 2. Install mitmproxy Certificate
- After running `img_proxy` (included in the distribution package), execute the `install_cert` program.
- Follow the on-screen instructions to install the certificate.
- Alternatively, after running the program, you can visit http://mitm.it in your web browser to download the certificate directly.

#### OS-Specific Certificate Installation
- **macOS**: Double-click the downloaded certificate (.pem) to add it to Keychain Access, then set it to 'Always Trust'.
- **Linux**: Add the downloaded certificate to the system certificate store (methods vary by distribution).
- **Windows**: Coming soon, not yet released.

## How to Use

1. Run the `img_proxy` executable from the distribution package.
   - macOS/Linux: Execute `./img_proxy` in the terminal.
2. The program will automatically configure your system proxy settings.
3. When you visit web pages in your browser, images will be automatically converted to WebP format.
4. To stop the program, press Ctrl+C in the console window or close the window.

## Important Notes

- When the program is terminated, proxy settings will be automatically restored to their original state.
- Carbon emission logs are stored in the server database.
- It is recommended to close all previously open browser windows before running the program.
- Some domains may not function correctly due to certificate issues.

## Troubleshooting

- **Certificate Error**: If the certificate is not installed correctly, run the `install_cert` program or download and install the certificate from http://mitm.it.
- **Proxy Connection Error**: Check if other proxy programs are running and terminate them.
- **File Path Error**: Ensure the necessary file (e.g., `cdn_file_list.txt`) is present in the directory where the program is executed.
- **502 Bad Gateway**: For domains encountering this error, it is recommended to close the program before accessing them.

## Additional Information

- This program uses mitmproxy to detect image requests on web pages and serves PNG/JPEG images converted to WebP format.
- It includes a carbon emission tracking feature that automatically records carbon emissions when accessing web pages.
- It reduces data usage by utilizing WebP images stored in Google Cloud Storage.
- If you are the first to encounter a WebP image not yet stored in Google Cloud Storage, you enable its storage on the server, making it available for other users.
- It may not work correctly on some domains. The developers are working to resolve these issues.


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