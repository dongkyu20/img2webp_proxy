import os
import requests
from PIL import Image
from io import BytesIO
from google.cloud import storage
from google.cloud import firestore
import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "woven-province-411903-b1b12d94b3ac.json"


def download_image(image_url):
    """
    Download an image from the given URL.
    
    Args:
        image_url (str): URL of the image to download
        
    Returns:
        BytesIO: downloaded image data
    """
    try:
        response = requests.get("https://" + image_url, stream=True)
        response.raise_for_status()  # raise exception if error
        return BytesIO(response.content)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Image download error: {e}")

def convert_to_webp(image_data, quality=95, lossless=True):
    """
    Convert an image to WebP format while maintaining transparency.

    Args:
        image_data (BytesIO): original image data
        quality (int): WebP conversion quality (0-100). lossless=True ignores this.
        lossless (bool): lossless compression (preferred for transparency)

    Returns:
        BytesIO: WebP converted image data (maintains transparency)
    """
    try:
        img = Image.open(image_data)
        output = BytesIO()
        img.save(output, format="WEBP", quality=quality, lossless=lossless)
        output.seek(0)
        return output
    except Exception as e:
        raise Exception(f"WebP conversion error (attempting to maintain transparency): {e}")

def upload_to_gcs(webp_data, bucket_name, domain, filename_base, original_path_query):
    """
    Upload WebP image to Google Cloud Storage.
    
    Args:
        webp_data (BytesIO): WebP image data
        bucket_name (str): GCS bucket name
        
    Returns:
        str: uploaded file CDN URL
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        blob = bucket.blob(f"{domain}/{original_path_query}{filename_base}.webp")
        blob.upload_from_file(webp_data, content_type='image/webp')
        
        cdn_url = f"https://storage.cloud.google.com/{bucket_name}/{domain}/{original_path_query}{filename_base}.webp"
        
        return cdn_url
    except Exception as e:
        raise Exception(f"GCS upload error: {e}")

def save_url_to_gcs(domain, original_url, bucket_name):
    """
    Save original image URL to GCS bucket text file if original image size is smaller than WebP image size.
    
    Args:
        domain (str): image domain
        original_url (str): original image URL
        bucket_name (str): GCS bucket name
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        blob = bucket.blob('smaller_original_images.txt')
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if blob.exists():
            content = blob.download_as_text()
            rows = content.split('\n')
            for row in rows[1:]:
                if row and original_url in row:
                    print(f"URL already exists, not adding duplicate: {original_url}")
                    return
            content += f"\n{domain},{original_url},{timestamp}"
        else:
            content = f"domain,original_url,recorded_at\n{domain},{original_url},{timestamp}"
        
        blob.upload_from_string(content, content_type='text/plain')
        
        print(f"Original image URL saved to GCS: {original_url}")
    except Exception as e:
        print(f"Original image URL save error: {e}")


def process_image(domain, content_url, bucket_name, quality=95, filename_base=None, original_path_query=None):
    """
    Download image from URL, convert to WebP, and upload to GCS.
    
    Args:
        domain (str): domain where image is loaded
        content_url (str): image URL
        bucket_name (str): GCS bucket name
        quality (int): WebP conversion quality (0-100)
        destination_path (str, optional): GCS path and filename
        
    Returns:
        str: uploaded file CDN URL
    """
    try:
        # download image
        image_data = download_image(domain + content_url)
        
        # convert to WebP
        webp_data = convert_to_webp(image_data, quality)

        # original image size in bytes
        ori_size = len(image_data.getvalue())

        # WebP image size in bytes
        webp_size = len(webp_data.getvalue())

        if ori_size > webp_size:
            # upload to GCS
            upload_to_gcs(webp_data, bucket_name, domain, filename_base, original_path_query)
        else:
            full_content_url = "https://" + domain + content_url
            save_url_to_gcs(domain, full_content_url, bucket_name)
            
        return
    except Exception as e:
        raise Exception(f"image processing failed: {e}")
