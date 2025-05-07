## firestore db에서 원본 파일을 찾기. 실패하면 -1 반환(계산 x), 성공하면 파일의 크기 반환

import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def search_original_image_size(original_url: str, db: firestore.Client, app: firebase_admin.App) -> int:
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
        
        # 콜렉션의 모든 문서 가져오기
        docs = collection_ref.get()
        
        logger.info(f"원본 이미지 URL 검색: {original_url}")
        
        # 모든 문서를 순회하며 검색
        for doc in docs:
            doc_data = doc.to_dict()
            
            # 문서에 'networkRequests' 필드가 있는지 확인
            if 'networkRequests' not in doc_data:
                continue
            
            # networkRequests 배열의 각 항목 확인
            for resource in doc_data['networkRequests']:
                # URL이 일치하는지 확인
                if resource.get('url') == original_url:
                    # 발견하면 resourceSize 반환
                    size = resource.get('resourceSize', -1)
                    logger.info(f"원본 이미지 발견! URL: {original_url}, 크기: {size} 바이트")
                    return size
        
        # 물어보는 이미지를 발견하지 못함
        logger.warning(f"이미지를 발견하지 못함: {original_url}")
        return -1
        
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        return -1

# 테스트 코드
if __name__ == "__main__":
    # 테스트할 이미지 URL
    test_url = "https://www.trakya.edu.tr/files/anasayfa_kayan_resimler/320/1.webp"
    
    # 검색 실행
    size = search_original_image_size(test_url)
    
    if size > 0:
        print(f"발견된 이미지 크기: {size} 바이트")
    else:
        print("이미지를 발견하지 못했습니다.")
