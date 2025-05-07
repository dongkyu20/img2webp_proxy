import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import logging
import datetime

from search_ori_file import search_original_image_size

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Firebase 인증 정보 가져오기
# 사용하고 있는 인증 파일로 대체해야 함
cred_path = os.path.join(os.path.dirname(__file__),'..','..', 'ecarbon-57bf2-3de439977a33.json')

# Firebase 초기화 (이미 초기화된 경우 처리)
try:
    # 이미 초기화된 경우 기본 앱 가져오기
    app = firebase_admin.get_app()
except ValueError:
    # Firebase 앱이 아직 초기화되지 않은 경우
    cred = credentials.Certificate(cred_path)
    app = firebase_admin.initialize_app(cred)

# Firestore 데이터베이스 가져오기
db = firestore.client()

def find_webp_file_size(webp_path: str) -> int:
    """
    cdn_file_list.txt 파일에서 WebP 파일의 크기를 찾습니다.
    
    Args:
        webp_path (str): 검색할 WebP 파일 경로 (도메인/파일명 형식)
        
    Returns:
        int: 발견된 경우 WebP 파일의 크기(바이트), 발견되지 않은 경우 -1
    """
    try:
        # cdn_file_list.txt 파일 경로
        file_list_path = os.path.join(os.path.dirname(__file__),'..','..', 'cdn_file_list.txt')
        
        with open(file_list_path, 'r', encoding='utf-8') as file:
            for line in file:
                # 탭으로 구분된 형식이면 (파일경로	크기	단위)
                if '\t' in line and webp_path in line:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        # 두 번째 부분이 크기(바이트)
                        try:
                            size_bytes = int(parts[1].replace(' bytes', ''))
                            logger.info(f"WebP 파일 발견! 경로: {webp_path}, 크기: {size_bytes} 바이트")
                            return size_bytes
                        except ValueError:
                            logger.warning(f"WebP 파일 크기를 변환할 수 없음: {parts[1]}")
                # 탭이 없는 형식이면 (파일경로만 있는 경우)
                elif webp_path in line:
                    logger.warning(f"WebP 파일을 찾았지만 크기 정보가 없습니다: {line.strip()}")
                    return -1
        
        logger.warning(f"WebP 파일을 찾을 수 없음: {webp_path}")
        return -1
        
    except Exception as e:
        logger.error(f"WebP 파일 크기 검색 중 오류 발생: {e}")
        return -1

def calc_reduction(original_url: str, webp_path: str) -> dict:
    """
    원본 이미지와 WebP 이미지의 크기 차이를 계산합니다.
    
    Args:
        original_url (str): 원본 이미지 URL
        webp_path (str): WebP 파일 경로 (도메인/파일명 형식)
        
    Returns:
        dict: 계산 결과
            {
                'original_size': 원본 크기(바이트),
                'webp_size': WebP 크기(바이트),
                'reduction_bytes': 절감된 크기(바이트),
                'reduction_percent': 절감된 비율(%),
                'success': 성공 여부
            }
    """
    result = {
        'original_size': -1,
        'webp_size': -1,
        'reduction_bytes': 0,
        'reduction_percent': 0,
        'success': False,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    # 원본 이미지 크기 검색
    original_size = search_original_image_size(original_url, db, app)
    result['original_size'] = original_size
    
    # WebP 파일 크기 검색
    webp_size = find_webp_file_size(webp_path)
    result['webp_size'] = webp_size
    
    # 두 파일이 모두 발견되었는지 확인
    if original_size > 0 and webp_size > 0:
        result['success'] = True
        result['reduction_bytes'] = original_size - webp_size
        result['reduction_percent'] = round((1 - (webp_size / original_size)) * 100, 2)
        
        logger.info(f"""계산 결과:
            원본 크기: {original_size} 바이트
            WebP 크기: {webp_size} 바이트
            절감된 크기: {result['reduction_bytes']} 바이트
            절감된 비율: {result['reduction_percent']}%
        """)
    else:
        logger.warning(f"계산 실패: 원본 크기({original_size} 바이트) 또는 WebP 크기({webp_size} 바이트)가 유효하지 않습니다.")
    
    return result

def save_reduction_to_firestore(result: dict, domain: str, original_url: str, webp_path: str) -> str:
    """
    감소량 계산 결과를 Firestore에 저장합니다.
    
    Args:
        result (dict): 계산 결과
        domain (str): 도메인
        original_url (str): 원본 이미지 URL
        webp_path (str): WebP 파일 경로
        
    Returns:
        str: 저장된 문서 ID
    """
    try:
        # reduction_logs 콜렉션 가져오기
        collection_ref = db.collection('reduction_logs')
        
        # 저장할 데이터 구성
        data = {
            'domain': domain,
            'original_url': original_url,
            'webp_path': webp_path,
            'original_size': result['original_size'],
            'webp_size': result['webp_size'],
            'reduction_bytes': result['reduction_bytes'],
            'reduction_percent': result['reduction_percent'],
            'success': result['success'],
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        
        # Firestore에 문서 추가
        doc_ref = collection_ref.document("유저 아이디 넣기").set(data, merge=True)
        
        logger.info(f"감소량 계산 결과가 Firestore에 저장되었습니다. 문서 ID: {doc_ref.id}")
        
        return doc_ref.id
        
    except Exception as e:
        logger.error(f"Firestore 저장 중 오류 발생: {e}")
        return ""

# 메인 함수 - 전체 프로세스를 관리
def process_reduction(domain: str, original_url: str, webp_filename: str) -> dict:
    """
    원본 이미지와 WebP 이미지의 크기 차이를 계산하고 Firestore에 저장합니다.
    
    Args:
        domain (str): 도메인
        original_url (str): 원본 이미지 URL
        webp_filename (str): WebP 파일명
        
    Returns:
        dict: 계산 결과
    """
    # WebP 파일 경로 구성 (domain/webp_filename)
    webp_path = f"{domain}/{webp_filename}"
    
    # 감소량 계산
    result = calc_reduction(original_url, webp_path)
    
    # 계산 결과가 성공적이면 Firestore에 저장
    if result['success']:
        doc_id = save_reduction_to_firestore(result, domain, original_url, webp_path)
        if doc_id:
            logger.info(f"모든 프로세스가 성공적으로 완료되었습니다. Firestore 문서 ID: {doc_id}")
        else:
            logger.warning("계산은 성공했지만 Firestore 저장에 실패했습니다.")
    else:
        logger.warning("크기 비교 계산에 실패했습니다.")
    
    return result


# 테스트 코드
if __name__ == "__main__":
    # 테스트를 위한 예제 데이터
    test_domain = "www.korea.ac.kr"
    test_original_url = "https://www.korea.ac.kr/sites/ko/images/common/logo_w.png"
    test_webp_filename = "logo_w.webp"
    
    # 테스트 실행
    print(f"\n[테스트 시작] 원본 URL: {test_original_url}")
    print(f"WebP 파일: {test_domain}/{test_webp_filename}\n")
    
    result = process_reduction(test_domain, test_original_url, test_webp_filename)
    
    if result['success']:
        print(f"\n[결과 요약]")
        print(f"• 원본 크기: {result['original_size']:,} 바이트")
        print(f"• WebP 크기: {result['webp_size']:,} 바이트")
        print(f"• 절감된 크기: {result['reduction_bytes']:,} 바이트")
        print(f"• 절감된 비율: {result['reduction_percent']}%\n")
    else:
        print(f"\n[결과] 비교 계산 실패\n")