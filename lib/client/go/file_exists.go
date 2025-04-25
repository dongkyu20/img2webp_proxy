package file_exists

import (
	"context"
	"fmt"
	"io"
	"os"
	"time"

	"cloud.google.com/go/storage"
	"google.golang.org/api/iterator"
	"google.golang.org/api/option"
)

func init() {
	// 환경 변수 설정
	os.Setenv("REQUESTS_CA_BUNDLE", "mitmproxy-ca-cert.pem")
	os.Setenv("GOOGLE_APPLICATION_CREDENTIALS", "woven-province-411903-b1b12d94b3ac.json")

	// 기본 버킷 이름과 출력 파일을 지정할 수 있습니다
	bucketName := "your-bucket-name" // 실제 버킷 이름으로 변경하세요
	outputFile := "cdn_file_list.txt"

	// 타임아웃 설정 (선택적)
	var timeout time.Duration // nil 값을 사용하려면 빈 값으로 둡니다

	// 함수 호출
	listBlobsInBucket(bucketName, outputFile, timeout)
}

func listBlobsInBucket(bucketName, outputFile string, timeout time.Duration) {
	ctx := context.Background()

	// 타임아웃 설정이 있는 경우 context에 적용
	if timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, timeout)
		defer cancel()
	}

	// 스토리지 클라이언트 초기화
	client, err := storage.NewClient(ctx, option.WithCredentialsFile(os.Getenv("GOOGLE_APPLICATION_CREDENTIALS")))
	if err != nil {
		fmt.Printf("스토리지 클라이언트 생성 오류: %v\n", err)
		return
	}
	defer client.Close()

	// 출력 파일 생성
	file, err := os.Create(outputFile)
	if err != nil {
		fmt.Printf("파일 생성 오류: %v\n", err)
		return
	}
	defer file.Close()

	fmt.Printf("'%s' 버킷의 파일 목록:\n", bucketName)

	// 버킷의 객체(blob) 목록 가져오기
	it := client.Bucket(bucketName).Objects(ctx, nil)

	foundFiles := false
	for {
		// 다음 객체 가져오기
		attrs, err := it.Next()
		if err == iterator.Done {
			break
		}
		if err != nil {
			if isForbiddenError(err) {
				fmt.Printf("오류: 버킷 '%s'에 접근할 권한이 없습니다. IAM 권한을 확인하세요.\n", bucketName)
			} else if isNotFoundError(err) {
				fmt.Printf("오류: 버킷 '%s'을(를) 찾을 수 없습니다.\n", bucketName)
			} else {
				fmt.Printf("객체 목록 가져오기 오류: %v\n", err)
			}
			return
		}

		// 객체 이름 출력 및 파일에 저장
		blobName := attrs.Name
		fmt.Printf("- %s\n", blobName)
		io.WriteString(file, blobName+"\n")
		foundFiles = true
	}

	if !foundFiles {
		fmt.Println("  (버킷에 파일이 없습니다)")
		io.WriteString(file, "(버킷에 파일이 없습니다)\n")
	}
}

// 오류가 권한 거부인지 확인
func isForbiddenError(err error) bool {
	return err.Error() == "storage: bucket access is forbidden"
}

// 오류가 찾을 수 없음인지 확인
func isNotFoundError(err error) bool {
	return err.Error() == "storage: bucket doesn't exist"
}
