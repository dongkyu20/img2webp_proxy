# -*- coding: utf-8 -*-
from mitmproxy import http
from mitmproxy import ctx
import re
import os
from urllib.parse import urlparse
import requests
import json
import datetime
import threading
import time
from file_exists import list_blobs_in_bucket
from google.cloud import storage
from google.oauth2 import service_account

# os.environ["REQUESTS_CA_BUNDLE"] = "mitmproxy-ca-cert.pem"
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "woven-province-411903-b1b12d94b3ac.json"
# Change from absolute paths to relative paths
os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mitmproxy-ca-cert.pem")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "woven-province-411903-b1b12d94b3ac.json")

# 서비스 계정 키 파일 경로
KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "woven-province-411903-b1b12d94b3ac.json")

os.environ["HTTP_PROXY"] = "http://127.0.0.1:8227"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:8227"


# --- User Setting ---
CDN_BASE_URL = "https://storage.cloud.google.com/cdn.ecarbon.kr" # Actual CDN address

# --- Remote Logging Setting ---
ENABLE_REMOTE_LOGGING = True # Set to True to enable remote logging
# Important: Change the IP address below to the actual IP address of PC B!
REMOTE_LOG_SERVER_URL = "http://211.253.31.134:5000/log"
REMOTE_LOG_TIMEOUT_SECONDS = 0.1 # Remote logging request timeout
# --- Remote Logging Setting End ---

# --- User Setting End ---
ORIGINAL_IMAGE_EXT_REGEX = re.compile(r"\.(png|jpe?g)(\?.*)?$|[_=](png|jpe?g)($|\?|&)|atchFileId=.*_(png|jpe?g)($|\?|&)", re.IGNORECASE)

# GCS bucket name
BUCKET_NAME = "cdn.ecarbon.kr"
# File list update interval (seconds)
UPDATE_INTERVAL = 1800  # 30 minutes = 1800 seconds
# Smaller images list file name
SMALLER_IMAGES_FILENAME = "smaller_original_images.txt"
# Smaller images list local file path
SMALLER_IMAGES_LOCAL_PATH = "smaller_original_images.txt"

## Exception handling list, will be updated...
BYPASS_DOMAINS = [
    "donga.ac.kr",
    "bufs.ac.kr",
    "www.ahnlab.com"
]

# CDN file list update function
def update_cdn_file_list_periodically():
    """Update GCS bucket file list every 30 minutes."""
    while True:
        try:
            ctx.log.info(f"[CDN File List] CDN file list update started: {datetime.datetime.now().isoformat()}")
            list_blobs_in_bucket(BUCKET_NAME)
            ctx.log.info(f"[CDN File List] CDN file list update completed: {datetime.datetime.now().isoformat()}")
        except Exception as e:
            ctx.log.error(f"[CDN File List] CDN file list update error: {e}")
        
        # Wait for the specified time (30 minutes)
        time.sleep(UPDATE_INTERVAL)

# Download smaller_original_images.txt file from GCS bucket
def download_smaller_images_list(bucket_name, timeout=None):
    """Download smaller_original_images.txt file from GCS bucket."""
    try:
        # 서비스 계정 자격 증명 명시적 로드
        credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
        
        # Initialize client with explicit credentials
        storage_client = storage.Client(credentials=credentials)
        # set timeout
        storage_client._http.timeout = timeout if timeout else None
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(SMALLER_IMAGES_FILENAME)
        
        # Check if the file exists
        if blob.exists():
            # Download the file
            blob.download_to_filename(SMALLER_IMAGES_LOCAL_PATH)
            ctx.log.info(f"[Smaller Images] {SMALLER_IMAGES_FILENAME} file downloaded successfully")
            return True
        else:
            ctx.log.warn(f"[Smaller Images] {SMALLER_IMAGES_FILENAME} file not found in bucket")
            # Create an empty file locally
            with open(SMALLER_IMAGES_LOCAL_PATH, 'w', encoding='utf-8') as f:
                f.write("domain,original_url,recorded_at\n")
            return False
    except Exception as e:
        ctx.log.error(f"[Smaller Images] smaller_original_images.txt download error: {e}")
        return False

# Update smaller_original_images.txt file periodically
def update_smaller_images_list_periodically():
    """Update smaller_original_images.txt file periodically."""
    while True:
        try:
            ctx.log.info(f"[Smaller Images] smaller_original_images.txt update started: {datetime.datetime.now().isoformat()}")
            download_smaller_images_list(BUCKET_NAME)
            ctx.log.info(f"[Smaller Images] smaller_original_images.txt update completed: {datetime.datetime.now().isoformat()}")
        except Exception as e:
            ctx.log.error(f"[Smaller Images] smaller_original_images.txt update error: {e}")
        
        # Wait for the specified time
        time.sleep(UPDATE_INTERVAL)

# Program startup initial file list update - run in the background thread to prevent blocking
def init_cdn_file_list():
    ctx.log.info("[CDN File List] Initial CDN file list creation...")
    try:
        list_blobs_in_bucket(BUCKET_NAME, timeout=15)
        ctx.log.info("[CDN File List] Initial CDN file list created")
        
        # Download smaller_original_images.txt file from GCS bucket
        download_smaller_images_list(BUCKET_NAME, timeout=15)
    except Exception as e:
        ctx.log.error(f"[CDN File List] initial CDN file list creation error: {e}")

# Initialize CDN file list at program start - run in the background thread to prevent blocking
init_thread = threading.Thread(target=init_cdn_file_list, daemon=True)
init_thread.start()
ctx.log.info("[CDN File List] initial CDN file list creation thread started")

# Periodic CDN file list update thread
updater_thread = threading.Thread(target=update_cdn_file_list_periodically, daemon=True)
updater_thread.start()
ctx.log.info("[CDN File List] periodic CDN file list update thread started")

# Periodic smaller_original_images.txt update thread
smaller_images_thread = threading.Thread(target=update_smaller_images_list_periodically, daemon=True)
smaller_images_thread.start()
ctx.log.info("[Smaller Images] periodic smaller_original_images.txt update thread started")

# Find URL in file
def search_path(file_path, Target_URL):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, 1):
                line = line.strip()  # Remove trailing whitespace and newline characters
                if Target_URL in line:
                    return True
            # All lines checked but not found
            return False
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

# Check if the original image URL is in 'smaller_original_images.txt'
def is_smaller_original_image(original_url):
    """Check if the original image URL is in 'smaller_original_images.txt'"""
    try:
        with open(SMALLER_IMAGES_LOCAL_PATH, 'r', encoding='utf-8') as file:
            # Skip the first line (header)
            next(file, None)
            
            for line in file:
                if line.strip() and original_url in line:
                    return True
        return False
    except FileNotFoundError:
        ctx.log.warn(f"[Smaller Images] File not found: {SMALLER_IMAGES_LOCAL_PATH}")
        return False
    except Exception as e:
        ctx.log.error(f"[Smaller Images] Error reading file: {e}")
        return False




# --- Remote logging function ---
def send_log_to_remote(level, message, original_path_full, domain, original_filename, filename_base, original_path_query):
    """Send log message to specified server using POST request."""
    if not ENABLE_REMOTE_LOGGING:
        return
    try:
        payload = {
            "level": level,
            "message": message,
            "origin_url": original_path_full,
            "domain": domain,
            "original_filename": original_filename,
            "filename_base": filename_base,
            "original_path_query": original_path_query,
            "timestamp": datetime.datetime.now().isoformat() # Current time added
        }
        headers = {'Content-Type': 'application/json'}

        # Set proxy to None to avoid using proxy
        proxies = {
          "http": None,
          "https": None,
        }

        # ctx.log.info(f"Attempting to send log DIRECTLY to {REMOTE_LOG_SERVER_URL}") # 디버깅 로그 추가 (선택사항)

        response = requests.post(
            REMOTE_LOG_SERVER_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=REMOTE_LOG_TIMEOUT_SECONDS,
            proxies=proxies
        )

        if response.status_code != 200:
            ctx.log.error(f"[Remote Logging Error] Failed to send log. Server responded with {response.status_code}")
    except requests.exceptions.RequestException as e:
        # Improve error log: include proxy information in the full error output
        ctx.log.error(f"[Remote Logging Error] Failed to send log to {REMOTE_LOG_SERVER_URL}: {e}")
    except Exception as e:
        ctx.log.error(f"[Remote Logging Error] Unexpected error during remote logging: {e}")



class CheckAndLogMissingWebp:
    ctx.options.ignore_hosts = BYPASS_DOMAINS
    def request(self, flow: http.HTTPFlow) -> None:    
        match = ORIGINAL_IMAGE_EXT_REGEX.search(flow.request.path)
        if match:
            domain = flow.request.pretty_host
            original_path_full = flow.request.path # Original URL
            parsed_url = urlparse(original_path_full)
            original_path_no_query = parsed_url.path
            original_path_query = parsed_url.query
            original_filename = os.path.basename(original_path_no_query)
            filename_base, _ = os.path.splitext(original_filename)
            webp_filename = original_path_query + filename_base + ".webp"
            webp_path = f"{domain}/{webp_filename}"

            # Path rule : CDN_BASE_URL / domain / original path query + original filename.webp
            if CDN_BASE_URL.endswith('/'):
                cdn_webp_url = CDN_BASE_URL + domain + '/' + webp_filename
            else:
                cdn_webp_url = CDN_BASE_URL + '/' + domain + '/' + webp_filename

            try:
                # Check if the original image is in 'smaller_original_images.txt'
                if is_smaller_original_image(original_path_full):
                    print(f"[Smaller Original] Original image found in smaller_original_images.txt: {original_path_full}")
                    # # If the original image is in 'smaller_original_images.txt', use the original image
                    # flow.response = http.Response.make(
                    #     302,  # Status code: Found (Temporary Redirect)
                    #     b"",  # Response body
                    #     {
                    #     "Location": original_path_full, # Use the original image URL
                    #     "Content-Type": "text/plain",
                    #     "Cache-Control": "public, max-age=3600",
                    #     }
                    # )
                elif search_path("cdn_file_list.txt", webp_path):
                    print(f"\n\n{cdn_webp_url} is in list!\n\n")
                    flow.response = http.Response.make(
                        302,  # Status code: Found (Temporary Redirect)
                        b"",  # Response body
                        {
                        "Location": cdn_webp_url, # Final CDN URL (only .webp filename)
                        "Content-Type": "text/plain",
                        "Cache-Control": "public, max-age=3600",
                        # "Pragma": "no-cache",
                        # "Expires": "0",
                        }
                    )
                    log_message = (
                        f"[Found WEBP] Found at {cdn_webp_url} "
                        f"(Original: {original_path_full})"
                    )
                    send_log_to_remote("SUCCESS", log_message, original_path_full, domain, original_filename, filename_base, original_path_query)
                else:
                    log_message = (
                        f"[Missing WEBP] Not found at {cdn_webp_url} "
                        f"(Original: {original_path_full})"
                    )
                    # Local log output
                    ctx.log.warn(log_message)
                    # Send log to remote server
                    send_log_to_remote("WARN", log_message, original_path_full, domain, original_filename, filename_base, original_path_query)
            except Exception as e:
                log_message = (
                    f"catch error {e}"
                    f"(Original: {original_path_full})"
                    f"(cdn_webp_url: {cdn_webp_url})"
                )
                # Local log output
                ctx.log.error(log_message)
                # Send log to remote server
                send_log_to_remote("ERROR", log_message, original_path_full, domain, original_filename, filename_base, original_path_query)

addons = [
    CheckAndLogMissingWebp()
]