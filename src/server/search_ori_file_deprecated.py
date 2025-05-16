

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
    Search for the original image size in the weekly_measurements collection of the Firestore database.
    
    Args:
        original_url (str): URL of the original image
        
    """
    try:
        # collection instance
        collection_ref = db.collection('weekly_measurements')
        
        # get all documents from collection
        docs = collection_ref.get()
        
        logger.info(f"original image URL search: {original_url}")
        
        # loop through all documents
        for doc in docs:
            doc_data = doc.to_dict()
            
            # check if 'networkRequests' field exists
            if 'networkRequests' not in doc_data:
                continue
            
            # loop through each item in networkRequests array
            for resource in doc_data['networkRequests']:
                # check if URL matches
                if resource.get('url') == original_url:
                    # return resourceSize if found
                    size = resource.get('resourceSize', -1)
                    logger.info(f"original image found! URL: {original_url}, size: {size} bytes")
                    return size
        
        # not found original image
        logger.warning(f"original image not found: {original_url}")
        return -1
        
    except Exception as e:
        logger.error(f"error: {e}")
        return -1

# test code
if __name__ == "__main__":
    # test image URL
    test_url = "https://www.trakya.edu.tr/files/anasayfa_kayan_resimler/320/1.webp"
    
    # search execution
    size = search_original_image_size(test_url)
    
    if size > 0:
        print(f"original image size: {size} bytes")
    else:
        print("original image not found")
