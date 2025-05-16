import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import logging
import datetime

from search_ori_file import search_original_image_size

# logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Firebase authentication information
cred_path = os.path.join(os.path.dirname(__file__),'..','..', 'ecarbon-57bf2-3de439977a33.json')

# Firebase initialization
try:
    app = firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate(cred_path)
    app = firebase_admin.initialize_app(cred)

# Firestore database
db = firestore.client()

def find_webp_file_size(webp_path: str) -> int:
    """
    Find the size of the WebP file in the cdn_file_list.txt file.
    
    Args:
        webp_path (str): WebP file path (domain/filename format)
        
    Returns:
        int: WebP file size in bytes if found, -1 if not found
    """
    try:
        file_list_path = os.path.join(os.path.dirname(__file__),'..','..', 'cdn_file_list.txt')
        
        with open(file_list_path, 'r', encoding='utf-8') as file:
            for line in file:
                if '\t' in line and webp_path in line:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        try:
                            size_bytes = int(parts[1].replace(' bytes', ''))
                            logger.info(f"WebP file found! Path: {webp_path}, Size: {size_bytes} bytes")
                            return size_bytes
                        except ValueError:
                            logger.warning(f"WebP file size conversion failed: {parts[1]}")
                elif webp_path in line:
                    logger.warning(f"WebP file found but size information is missing: {line.strip()}")
                    return -1
        
        logger.warning(f"WebP file not found: {webp_path}")
        return -1
        
    except Exception as e:
        logger.error(f"WebP file size search error: {e}")
        return -1

def calc_reduction(original_url: str, webp_path: str) -> dict:
    """
    Calculate the size difference between the original image and the WebP image.
    
    Args:
        original_url (str): Original image URL
        webp_path (str): WebP file path (domain/filename format)
        
    Returns:
        dict: Calculation result
            {
                'original_size': original size in bytes,
                'webp_size': WebP size in bytes,
                'reduction_bytes': reduction in bytes,
                'reduction_percent': reduction percentage,
                'success': success flag
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
    
    # search original image size
    original_size = search_original_image_size(original_url, db, app)
    result['original_size'] = original_size
    
    # search webp file size
    webp_size = find_webp_file_size(webp_path)
    result['webp_size'] = webp_size
    
    # check if both files are found
    if original_size > 0 and webp_size > 0:
        result['success'] = True
        result['reduction_bytes'] = original_size - webp_size
        result['reduction_percent'] = round((1 - (webp_size / original_size)) * 100, 2)
        
        logger.info(f"""Calculation result:
            Original size: {original_size} bytes
            WebP size: {webp_size} bytes
            Reduction in size: {result['reduction_bytes']} bytes
            Reduction percentage: {result['reduction_percent']}%
        """)
    else:
        logger.warning(f"Calculation failed: Original size ({original_size} bytes) or WebP size ({webp_size} bytes) is invalid.")
    
    return result

def save_reduction_to_firestore(result: dict, domain: str, original_url: str, webp_path: str) -> str:
    """
    Save the calculation result to Firestore.
    
    Args:
        result (dict): Calculation result
        domain (str): Domain
        original_url (str): Original image URL
        webp_path (str): WebP file path
        
    Returns:
        str: Saved document ID
    """
    try:
        # reduction_logs collection
        collection_ref = db.collection('reduction_logs')
        
        # data to save
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
        
        # add document to Firestore
        doc_ref = collection_ref.document("user_id").set(data, merge=True)
        
        logger.info(f"Calculation result saved to Firestore. Document ID: {doc_ref.id}")
        
        return doc_ref.id
        
    except Exception as e:
        logger.error(f"Firestore storage error: {e}")
        return ""

# main function - manage entire process
def process_reduction(domain: str, original_url: str, webp_filename: str) -> dict:
    """
    Calculate the size difference between the original image and the WebP image and save it to Firestore.
    
    Args:
        domain (str): Domain
        original_url (str): Original image URL
        webp_filename (str): WebP file name
        
    Returns:
        dict: Calculation result
    """
    # WebP file path configuration (domain/webp_filename)
    webp_path = f"{domain}/{webp_filename}"
    
    # Calculate the size difference between the original image and the WebP image
    result = calc_reduction(original_url, webp_path)
    
    # If the calculation is successful, save the result to Firestore
    if result['success']:
        doc_id = save_reduction_to_firestore(result, domain, original_url, webp_path)
        if doc_id:
            logger.info(f"All processes completed successfully. Firestore document ID: {doc_id}")
        else:
            logger.warning("Calculation was successful but Firestore storage failed.")
    else:
        logger.warning("Size comparison calculation failed.")
    
    return result


# test code
if __name__ == "__main__":
    # test data
    test_domain = "www.korea.ac.kr"
    test_original_url = "https://www.korea.ac.kr/sites/ko/images/common/logo_w.png"
    test_webp_filename = "logo_w.webp"
    
    # test execution
    print(f"\n[Test Start] Original URL: {test_original_url}")
    print(f"WebP file: {test_domain}/{test_webp_filename}\n")
    
    result = process_reduction(test_domain, test_original_url, test_webp_filename)
    
    if result['success']:
        print(f"\n[Result Summary]")
        print(f"• Original size: {result['original_size']:,} bytes")
        print(f"• WebP size: {result['webp_size']:,} bytes")
        print(f"• Reduction in size: {result['reduction_bytes']:,} bytes")
        print(f"• Reduction percentage: {result['reduction_percent']}%\n")
    else:
        print(f"\n[Result] Size comparison calculation failed\n")