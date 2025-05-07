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
            local_cred_path = os.path.join(os.path.dirname(__file__), '..','..', 'ecarbon-57bf2-3de439977a33.json')

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


def search_original_image_size_efficient(original_url: str, db: firestore.Client) -> int:
    """
    파이어스토어 DB의 weekly_measurements 콜렉션에서 'requestedUrls' 필드를 사용하여
    원본 이미지 URL에 해당하는 리소스 크기를 검색합니다. (효율적인 방식)

    이 함수를 사용하기 위해서는 Firestore 문서에 'requestedUrls' (URL 문자열 배열) 필드가
    추가되어 있어야 합니다.

    Args:
        original_url (str): 검색할 원본 이미지 URL
        db (firestore.Client): Firestore 클라이언트 인스턴스

    Returns:
        int: 발견된 경우 이미지의 크기(바이트), 발견되지 않은 경우 -1
    """
    try:
        # 콜렉션 인스턴스 가져오기
        collection_ref = db.collection('weekly_measurements')

        # 'requestedUrls' 필드에 original_url을 포함하는 문서 검색
        query = collection_ref.where('requestedUrls', 'array-contains', original_url)
        docs = query.stream() # stream()을 사용하여 결과를 이터레이터로 받음

        logger.info(f"효율적 검색 시작 - 원본 이미지 URL: {original_url}")

        # 검색된 문서들을 순회 (일반적으로 URL이 고유하다면 하나 또는 소수의 문서만 반환됨)
        for doc in docs:
            doc_data = doc.to_dict()

            if 'networkRequests' not in doc_data:
                continue

            # networkRequests 배열의 각 항목 확인하여 정확한 resourceSize 찾기
            for resource in doc_data['networkRequests']:
                if resource.get('url') == original_url:
                    size = resource.get('resourceSize', -1)
                    logger.info(f"원본 이미지 발견! URL: {original_url}, 크기: {size} 바이트 (문서 ID: {doc.id})")
                    return size # 첫 번째 일치하는 항목 반환

        # 이미지를 발견하지 못함
        logger.warning(f"이미지를 발견하지 못함 (효율적 검색): {original_url}")
        return -1

    except Exception as e:
        logger.error(f"오류 발생 (효율적 검색): {e}")
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

        # print("\n--- 현재 비효율적인 방식 테스트 (search_original_image_size) ---")
        
        # # 1. 사용자가 제공한 URL로 테스트 (데이터가 없으면 못 찾음)
        # print(f"\n테스트 1: 사용자 제공 URL ({test_url_from_user})")
        # size1 = search_original_image_size(test_url_from_user, _test_db, _test_app)
        # if size1 != -1:
        #     print(f"  결과: 발견된 이미지 크기 = {size1} 바이트")
        # else:
        #     print(f"  결과: 이미지를 발견하지 못했거나 오류 발생.")

        # # 2. 존재할 것으로 예상되는 URL로 테스트 (실제 데이터에 따라 결과 달라짐)
        # print(f"\n테스트 2: 존재 예상 URL ({test_url_expected_to_exist})")
        # size2 = search_original_image_size(test_url_expected_to_exist, _test_db, _test_app)
        # if size2 != -1:
        #     print(f"  결과: 발견된 이미지 크기 = {size2} 바이트")
        # else:
        #     print(f"  결과: 이미지를 발견하지 못했거나 오류 발생 (데이터 확인 필요).")

        # # 3. 존재하지 않을 것으로 예상되는 URL로 테스트
        # print(f"\n테스트 3: 미존재 예상 URL ({test_url_not_expected_to_exist})")
        # size3 = search_original_image_size(test_url_not_expected_to_exist, _test_db, _test_app)
        # if size3 == -1:
        #     print(f"  결과: 예상대로 이미지를 발견하지 못했습니다.")
        # else:
        #     print(f"  결과: 발견된 이미지 크기 = {size3} 바이트 (오류: 실제로는 없어야 함).")

        # --- 효율적인 방식 V1 테스트 (search_original_image_size_efficiently_v1) ---
        # 아래 테스트를 실행하려면 'all_resource_metadata' 컬렉션에 테스트 데이터가 미리 준비되어 있어야 합니다.
        # 예: Firestore 'all_resource_metadata' 컬렉션에 다음 문서가 있다고 가정:
        #   { "url": "https://www.korea.ac.kr/sites/ko/images/common/logo_w.png", "resourceSize": 12345 }
        #   { "url": "https://www.trakya.edu.tr/files/anasayfa_kayan_resimler/320/1.webp", "resourceSize": 67890 }
        
        print("\n\n--- 효율적인 방식 V1 테스트 (search_original_image_size_efficiently_v1) ---")
        print("     (주의: 'all_resource_metadata' 컬렉션에 테스트 데이터가 준비되어 있어야 합니다.)")

        # 1. 사용자가 제공한 URL로 효율적 검색 테스트
        print(f"\n테스트 4: 사용자 제공 URL ({test_url_from_user}) - 효율적 검색")
        eff_size1 = search_original_image_size_efficiently_v1(test_url_from_user, _test_db)
        if eff_size1 != -1:
            print(f"  결과: 발견된 이미지 크기 = {eff_size1} 바이트")
        else:
            print(f"  결과: 이미지를 발견하지 못했거나 오류 발생 ('all_resource_metadata' 컬렉션 확인 필요).")

        # 2. 존재할 것으로 예상되는 URL로 효율적 검색 테스트
        print(f"\n테스트 5: 존재 예상 URL ({test_url_expected_to_exist}) - 효율적 검색")
        eff_size2 = search_original_image_size_efficiently_v1(test_url_expected_to_exist, _test_db)
        if eff_size2 != -1:
            print(f"  결과: 발견된 이미지 크기 = {eff_size2} 바이트")
        else:
            print(f"  결과: 이미지를 발견하지 못했거나 오류 발생 ('all_resource_metadata' 컬렉션 확인 필요).")