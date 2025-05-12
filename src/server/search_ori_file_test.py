# search_ori_file.py
import os
import firebase_admin
from firebase_admin import credentials, firestore # firestore 임포트 추가
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 이 파일 단독 테스트 시 사용할 Firebase 앱 및 DB 클라이언트 (전역 변수)
_test_app = None
_test_db = None

def _initialize_firebase_for_test():
    """이 파일을 직접 실행하여 테스트할 때만 Firebase를 초기화합니다."""
    global _test_app, _test_db
    if not firebase_admin._apps:
        try:
            # 중요: 실제 서비스 계정 파일 경로로 변경하거나 환경 변수를 사용하세요.
            # 예: cred_path = "path/to/your/serviceAccountKey.json"
            # 또는 환경 변수 GOOGLE_APPLICATION_CREDENTIALS를 설정합니다.
            cred_path_env = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            
            # 아래는 로컬 테스트를 위한 예시 경로입니다. 실제 환경에 맞게 수정하세요.
            # 사용자님의 파일명을 예시로 사용: 'ecarbon-57bf2-3de439977a33.json'
            # 이 파일이 search_ori_file.py와 같은 디렉토리에 있다고 가정합니다.
            local_cred_path = os.path.join(os.path.dirname(__file__), 'ecarbon-57bf2-3de439977a33.json')

            if cred_path_env:
                logger.info(f"환경 변수 GOOGLE_APPLICATION_CREDENTIALS를 사용하여 Firebase 초기화 시도.")
                cred = credentials.ApplicationDefault()
            elif os.path.exists(local_cred_path):
                logger.info(f"로컬 경로의 인증 파일 '{local_cred_path}'를 사용하여 Firebase 초기화 시도.")
                cred = credentials.Certificate(local_cred_path)
            else:
                logger.error("Firebase 인증 파일을 찾을 수 없습니다. GOOGLE_APPLICATION_CREDENTIALS 환경 변수를 설정하거나, "
                               f"로컬 경로 '{local_cred_path}'에 인증 파일을 위치시켜주세요.")
                return

            _test_app = firebase_admin.initialize_app(cred)
            _test_db = firestore.client(_test_app)
            logger.info("테스트용 Firebase 앱이 성공적으로 초기화되었습니다.")

        except Exception as e:
            logger.error(f"테스트용 Firebase 초기화 중 오류 발생: {e}", exc_info=True)
    else:
        _test_app = firebase_admin.get_app()
        _test_db = firestore.client(_test_app)
        logger.info("이미 초기화된 Firebase 앱을 테스트용으로 사용합니다.")


def search_original_image_size(domain, original_url: str, db: firestore.Client, app: firebase_admin.App) -> int:
    """
    파이어스토어 DB의 weekly_measurements 콜렉션에서 원본 이미지 URL에 해당하는 리소스 크기를 검색합니다.
    
    Args:
        original_url (str): 검색할 원본 이미지 URL
        
    Returns:
        int: 발견된 경우 이미지의 크기(바이트), 발견되지 않은 경우 -1
    """
    try:
        # 콜렉션 인스턴스 가져오기
        collection_ref = db.collection('weekly_measurements')

        query = collection_ref.where('url', '==', 'https://' + domain + '/')
        docs = query.get()

        print(f"\n\ndomain: {domain}\n\n")

        print(f"\n\noriginal_url: {original_url}\n\n")
        found_documents = []
        for doc in docs:
            if doc.exists:
                found_documents.append({
                    "id": doc.id,  # 문서 ID (이름)
                    "data": doc.to_dict() # 문서 데이터 (선택 사항)
                })
            else:
                logger.warning(f"해당 URL의 문서를 찾을 수 없습니다: {original_url}")
                return -1
        
        doc_data = found_documents[-1].get('data')
        if 'networkRequests' not in doc_data:
            logger.warning(f"해당 URL의 문서에 networkRequests 필드가 없습니다: {original_url}")
            return -1

        for resource in doc_data['networkRequests']:
            # URL이 일치하는지 확인
            if resource.get('url') == original_url:
                # 발견하면 resourceSize 반환
                size = resource.get('resourceSize', -1)
                logger.info(f"원본 이미지 발견! URL: {original_url}, 크기: {size} 바이트")
                return size

        
        # 물어보는 이미지를 발견하지 못함
        print(f"이미지를 발견하지 못함: {original_url}")
        return -1
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return -1

# 이 파일을 직접 실행하여 테스트할 경우 사용되는 코드
if __name__ == "__main__":
    _initialize_firebase_for_test() # 테스트용 Firebase 초기화

    if not _test_db:
        logger.error("Firestore DB 클라이언트가 초기화되지 않아 테스트를 진행할 수 없습니다.")
    else:
        # 테스트할 이미지 URL (실제 Firestore 데이터 상황에 맞게 변경 필요)
        # 예시: 사용자가 제공한 URL
        test_url_from_user = "https://www.trakya.edu.tr/files/anasayfa_kayan_resimler/320/1.webp" 
        # 예시: Firestore 'weekly_measurements'에 존재할 것으로 예상되는 URL
        test_url_expected_to_exist = "https://www.korea.ac.kr/sites/ko/images/common/logo_w.png" 
        test_url_not_expected_to_exist = "https://example.com/this/url/does/not/exist.jpg"

        test_domain = "https://www.korea.ac.kr/"

        print(f"\n테스트 4: 사용자 제공 URL ({test_url_expected_to_exist})")
        eff_size1 = search_original_image_size(test_domain, test_url_expected_to_exist, _test_db, _test_app)
        if eff_size1 != -1:
            print(f"  결과: 발견된 이미지 크기 = {eff_size1} 바이트")
        else:
            print(f"  결과: 이미지를 발견하지 못했거나 오류 발생 ('all_resource_metadata' 컬렉션 확인 필요).")