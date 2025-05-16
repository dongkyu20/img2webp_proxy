# search_ori_file.py
import os
import firebase_admin
from firebase_admin import credentials, firestore
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

_test_app = None
_test_db = None

def _initialize_firebase_for_test():
    global _test_app, _test_db
    if not firebase_admin._apps:
        try:
            cred_path_env = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            
            local_cred_path = os.path.join(os.path.dirname(__file__), 'ecarbon-57bf2-3de439977a33.json')

            if cred_path_env:
                logger.info(f"Using environment variable GOOGLE_APPLICATION_CREDENTIALS to initialize Firebase.")
                cred = credentials.ApplicationDefault()
            elif os.path.exists(local_cred_path):
                logger.info(f"Using local credential file '{local_cred_path}' to initialize Firebase.")
                cred = credentials.Certificate(local_cred_path)
            else:
                logger.error("Firebase credential file not found. Set GOOGLE_APPLICATION_CREDENTIALS environment variable or "
                               f"place the credential file at '{local_cred_path}'.")
                return

            _test_app = firebase_admin.initialize_app(cred)
            _test_db = firestore.client(_test_app)
            logger.info("Firebase app initialized successfully.")

        except Exception as e:
            logger.error(f"Firebase app initialization error: {e}", exc_info=True)
    else:
        _test_app = firebase_admin.get_app()
        _test_db = firestore.client(_test_app)
        logger.info("Firebase app initialized successfully.")


def search_original_image_size(domain, original_url: str, db: firestore.Client, app: firebase_admin.App) -> int:
    """
    Search for the original image size in the weekly_measurements collection of the Firestore database.
    
    Args:
        original_url (str): Original image URL
        db (firestore.Client): Firestore client
        app (firebase_admin.App): Firebase app
    """
    try:
        collection_ref = db.collection('weekly_measurements')

        query = collection_ref.where('url', '==', 'https://' + domain + '/')
        docs = query.get()

        print(f"\n\ndomain: {domain}\n\n")

        print(f"\n\noriginal_url: {original_url}\n\n")
        found_documents = []
        for doc in docs:
            if doc.exists:
                found_documents.append({
                    "id": doc.id,
                    "data": doc.to_dict()
                })
            else:
                logger.warning(f"not found document: {original_url}")
                return -1
        
        doc_data = found_documents[-1].get('data')
        if 'networkRequests' not in doc_data:
            logger.warning(f"not found networkRequests field: {original_url}")
            return -1

        for resource in doc_data['networkRequests']:
            if resource.get('url') == original_url:
                size = resource.get('resourceSize', -1)
                logger.info(f"found original image! URL: {original_url}, size: {size} bytes")
                return size

        
        print(f"not found: {original_url}")
        return -1
        
    except Exception as e:
        print(f"error: {e}")
        return -1
# test code
if __name__ == "__main__":
    _initialize_firebase_for_test() # 테스트용 Firebase 초기화

    if not _test_db:
        logger.error("Firestore DB client not initialized. Unable to run test.")
    else:
        test_url_from_user = "https://www.trakya.edu.tr/files/anasayfa_kayan_resimler/320/1.webp" 
        test_url_expected_to_exist = "https://www.korea.ac.kr/sites/ko/images/common/logo_w.png" 
        test_url_not_expected_to_exist = "https://example.com/this/url/does/not/exist.jpg"

        test_domain = "https://www.korea.ac.kr/"

        print(f"\nTest 4: User-provided URL ({test_url_expected_to_exist})")
        eff_size1 = search_original_image_size(test_domain, test_url_expected_to_exist, _test_db, _test_app)
        if eff_size1 != -1:
            print(f"  Result: Found image size = {eff_size1} bytes")
        else:
            print(f"  Result: Image not found or error occurred ('all_resource_metadata' collection check required).")