// main.go
package main
import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"

	"cloud.google.com/go/storage"
	"github.com/google/martian/v3"
	"github.com/google/martian/v3/fifo"
	"github.com/google/martian/v3/httpspec"
	"github.com/google/martian/v3/mitm"
	"github.com/google/martian/v3/proxyutil"
	"google.golang.org/api/option"

	"github.com/dongkyu20/img2webp_proxy/lib/client/go/file_exists"
)

// 전역 설정
const (
	// 사용자 설정
	CDNBaseURL           = "https://storage.cloud.google.com/cdn.ecarbon.kr" // 실제 CDN 주소로 변경
	BucketName           = "cdn.ecarbon.kr"                                  // GCS 버킷 이름
	UpdateInterval       = 3600                                              // 파일 목록 업데이트 주기 (초) - 1시간

	// 원격 로깅 설정
	EnableRemoteLogging    = true                           // 원격 로깅 활성화 여부
	RemoteLogServerURL     = "http://211.253.31.134:5000/log" // PC B의 실제 IP 주소로 변경
	RemoteLogTimeoutSeconds = 1                            // 원격 로깅 요청 타임아웃
)

var (
	// 이미지 확장자를 확인하는 정규식
	originalImageExtRegex = regexp.MustCompile(`\.(png|jpe?g)(\?.*)?$|[_=](png|jpe?g)($|\?|&)|atchFileId=.*_(png|jpe?g)($|\?|&)`)
	
	// CDN 파일 목록을 저장하는 텍스트 파일
	cdnFileListPath = "cdn_file_list.txt"
	
	// CDN 파일 목록 업데이트를 위한 뮤텍스
	cdnFileListMutex sync.RWMutex
)

// 로그 메시지를 위한 구조체
type LogMessage struct {
	Level            string `json:"level"`
	Message          string `json:"message"`
	OriginURL        string `json:"origin_url"`
	Domain           string `json:"domain"`
	OriginalFilename string `json:"original_filename"`
	FilenameBase     string `json:"filename_base"`
	OriginalPathQuery string `json:"original_path_query"`
	Timestamp        string `json:"timestamp"`
}

// CDN 파일 목록을 초기화하는 함수
func initCDNFileList() {
	log.Println("[CDN File List] 초기 파일 목록 생성 중...")
	
	err := listBlobsInBucket(BucketName, 30)
	if err != nil {
		log.Printf("[CDN File List] 초기 파일 목록 생성 중 오류 발생: %v", err)
	} else {
		log.Println("[CDN File List] 초기 파일 목록 생성 완료")
	}
}

// CDN 파일 목록을 주기적으로 업데이트하는 함수
func updateCDNFileListPeriodically() {
	for {
		log.Printf("[CDN File List] 파일 목록 업데이트 시작: %s", time.Now().Format(time.RFC3339))
		
		err := listBlobsInBucket(BucketName, 0)
		if err != nil {
			log.Printf("[CDN File List] 파일 목록 업데이트 중 오류 발생: %v", err)
		} else {
			log.Printf("[CDN File List] 파일 목록 업데이트 완료: %s", time.Now().Format(time.RFC3339))
		}
		
		// 지정된 시간(1시간) 동안 대기
		time.Sleep(UpdateInterval * time.Second)
	}
}

// GCS 버킷의 파일 목록을 가져와 파일에 저장하는 함수
func listBlobsInBucket(bucketName string, timeout int) error {
	// 타임아웃 설정
	var ctx context.Context
	var cancel context.CancelFunc
	
	if timeout > 0 {
		ctx, cancel = context.WithTimeout(context.Background(), time.Duration(timeout)*time.Second)
		defer cancel()
	} else {
		ctx = context.Background()
	}
	
	// GCS 클라이언트 생성
	client, err := storage.NewClient(ctx, option.WithCredentialsFile("woven-province-411903-b1b12d94b3ac.json"))
	if err != nil {
		return fmt.Errorf("storage.NewClient 생성 오류: %v", err)
	}
	defer client.Close()
	
	// 버킷 접근
	bucket := client.Bucket(bucketName)
	
	// 파일 목록을 가져와 임시 파일에 저장
	tempFilePath := cdnFileListPath + ".tmp"
	tempFile, err := os.Create(tempFilePath)
	if err != nil {
		return fmt.Errorf("임시 파일 생성 오류: %v", err)
	}
	
	// 버킷의 모든 객체 목록 조회
	it := bucket.Objects(ctx, nil)
	count := 0
	
	for {
		attrs, err := it.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			tempFile.Close()
			return fmt.Errorf("객체 목록 조회 중 오류: %v", err)
		}
		
		// 파일 경로 저장
		_, err = tempFile.WriteString(attrs.Name + "\n")
		if err != nil {
			tempFile.Close()
			return fmt.Errorf("파일 쓰기 오류: %v", err)
		}
		
		count++
	}
	
	tempFile.Close()
	
	// 파일 목록 업데이트를 위한 락 획득
	cdnFileListMutex.Lock()
	defer cdnFileListMutex.Unlock()
	
	// 임시 파일을 실제 파일로 이동
	err = os.Rename(tempFilePath, cdnFileListPath)
	if err != nil {
		return fmt.Errorf("파일 이름 변경 오류: %v", err)
	}
	
	log.Printf("[CDN File List] %d개의 파일 목록을 저장했습니다", count)
	return nil
}

// 파일에서 특정 URL이 존재하는지 확인하는 함수
func searchPath(filePath, targetURL string) bool {
	cdnFileListMutex.RLock()
	defer cdnFileListMutex.RUnlock()
	
	file, err := os.Open(filePath)
	if err != nil {
		log.Printf("파일을 찾을 수 없습니다: %s, 오류: %v", filePath, err)
		return false
	}
	defer file.Close()
	
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == targetURL {
			return true
		}
	}
	
	if err := scanner.Err(); err != nil {
		log.Printf("파일 읽기 중 오류가 발생했습니다: %v", err)
	}
	
	return false
}

// 원격 서버로 로그 전송 함수
func sendLogToRemote(level, message, originalPathFull, domain, originalFilename, filenameBase, originalPathQuery string) {
	if !EnableRemoteLogging {
		return
	}
	
	logMessage := LogMessage{
		Level:            level,
		Message:          message,
		OriginURL:        originalPathFull,
		Domain:           domain,
		OriginalFilename: originalFilename,
		FilenameBase:     filenameBase,
		OriginalPathQuery: originalPathQuery,
		Timestamp:        time.Now().Format(time.RFC3339),
	}
	
	jsonData, err := json.Marshal(logMessage)
	if err != nil {
		log.Printf("[Remote Logging Error] JSON 마샬링 오류: %v", err)
		return
	}
	
	client := &http.Client{
		Timeout: time.Duration(RemoteLogTimeoutSeconds) * time.Second,
		Transport: &http.Transport{
			Proxy: nil, // 프록시 사용 안 함
		},
	}
	
	req, err := http.NewRequest("POST", RemoteLogServerURL, bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("[Remote Logging Error] 요청 생성 오류: %v", err)
		return
	}
	
	req.Header.Set("Content-Type", "application/json")
	
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("[Remote Logging Error] 로그 전송 실패 (%s): %v", RemoteLogServerURL, err)
		return
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		log.Printf("[Remote Logging Error] 로그 전송 실패. 서버 응답: %d", resp.StatusCode)
	}
}

// 이미지 요청을 처리하는 미들웨어
type CheckAndLogMissingWebp struct{}

// ModifyRequest는 미트프록시의 요청 수정 인터페이스를 구현합니다
func (m *CheckAndLogMissingWebp) ModifyRequest(req *http.Request) error {
	// 이미지 확장자를 가진 URL인지 확인
	if originalImageExtRegex.MatchString(req.URL.Path) {
		domain := req.Host
		originalPathFull := req.URL.String()
		parsedURL, _ := url.Parse(originalPathFull)
		originalPathNoQuery := parsedURL.Path
		originalPathQuery := parsedURL.RawQuery
		originalFilename := filepath.Base(originalPathNoQuery)
		filenameBase := strings.TrimSuffix(originalFilename, filepath.Ext(originalFilename))
		webpFilename := originalPathQuery + filenameBase + ".webp"
		webpPath := fmt.Sprintf("%s/%s", domain, webpFilename)
		
		var cdnWebpURL string
		if strings.HasSuffix(CDNBaseURL, "/") {
			cdnWebpURL = CDNBaseURL + domain + "/" + webpFilename
		} else {
			cdnWebpURL = CDNBaseURL + "/" + domain + "/" + webpFilename
		}
		
		try {
			if searchPath(cdnFileListPath, webpPath) {
				fmt.Printf("\n\n%s is in list!\n\n", cdnWebpURL)
				
				// 응답을 만들어 리다이렉트
				resp := proxyutil.NewResponse(302, nil, req)
				resp.Header.Set("Location", cdnWebpURL)
				resp.Header.Set("Content-Type", "text/plain")
				resp.Header.Set("Cache-Control", "no-cache, no-store, must-revalidate")
				resp.Header.Set("Pragma", "no-cache")
				resp.Header.Set("Expires", "0")
				
				ctx := martian.NewContext(req)
				ctx.SkipRoundTrip()
				ctx.SetResponse(resp)
			} else {
				logMessage := fmt.Sprintf("[Missing WEBP] Not found at %s (Original: %s)", cdnWebpURL, originalPathFull)
				log.Print(logMessage)
				sendLogToRemote("WARN", logMessage, originalPathFull, domain, originalFilename, filenameBase, originalPathQuery)
			}
		} catch (err error) {
			logMessage := fmt.Sprintf("catch error %v (Original: %s) (cdn_webp_url: %s)", err, originalPathFull, cdnWebpURL)
			log.Print(logMessage)
			sendLogToRemote("ERROR", logMessage, originalPathFull, domain, originalFilename, filenameBase, originalPathQuery)
		}
	}
	
	return nil
}

func main() {
	// 환경 변수 설정
	os.Setenv("REQUESTS_CA_BUNDLE", "mitmproxy-ca-cert.pem")
	os.Setenv("GOOGLE_APPLICATION_CREDENTIALS", "woven-province-411903-b1b12d94b3ac.json")
	
	// 초기화 및 주기적 업데이트를 위한 고루틴 시작
	go initCDNFileList()
	go updateCDNFileListPeriodically()
	
	// 프록시 생성
	p := martian.NewProxy()
	
	// TLS 설정
	tls, err := mitm.NewConfig("mitmproxy-ca-cert.pem", "mitmproxy-ca-key.pem")
	if err != nil {
		log.Fatalf("mitm.NewConfig 오류: %v", err)
	}
	
	p.SetMITM(tls)
	
	// 미들웨어 추가
	fg := fifo.NewGroup()
	fg.AddRequestModifier(&CheckAndLogMissingWebp{})
	p.SetRequestModifier(fg)
	
	// 프록시 서버 시작
	l, err := net.Listen("tcp", ":8080")
	if err != nil {
		log.Fatalf("net.Listen 오류: %v", err)
	}
	
	log.Println("프록시 서버가 8080 포트에서 실행 중입니다...")
	log.Fatal(http.Serve(l, p))
}