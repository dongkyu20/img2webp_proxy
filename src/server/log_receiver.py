# log_monitor_server.py (PC B에서 실행 - FastAPI 버전)
import datetime
from typing import Optional # Optional fields

from fastapi import FastAPI, HTTPException, status, BackgroundTasks # FastAPI classes
from pydantic import BaseModel, Field # data validation and default value handling
from convert_n_upload import process_image
from CalcReduction_n_upload import process_reduction
from file_exists import list_blobs_in_bucket

import threading
import time
import uvicorn # FastAPI server run

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "woven-province-411903-b1b12d94b3ac.json"

# --- Pydantic model definition ---
class LogEntry(BaseModel):
    level: Optional[str] = 'INFO' # default value
    message: Optional[str] = ''
    origin_url: Optional[str] = ''
    domain: Optional[str] = ''
    original_filename: Optional[str] = ''
    filename_base: Optional[str] = ''
    original_path_query: Optional[str] = ''
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.datetime.now().isoformat())

BUCKET_NAME = "cdn.ecarbon.kr"
UPDATE_INTERVAL = 1800
    

# init cdn file list
def init_cdn_file_list():
    print("[CDN File List] initial file list creation...")
    try:
        list_blobs_in_bucket(BUCKET_NAME, timeout=30)
        print("[CDN File List] initial file list creation completed")
    except Exception as e:
        print(f"[CDN File List] initial file list creation error: {e}")

# CDN file list update periodically
def update_cdn_file_list_periodically():
    while True:
        try:
            print(f"[CDN File List] file list update started: {datetime.datetime.now().isoformat()}")
            list_blobs_in_bucket(BUCKET_NAME)
            print(f"[CDN File List] file list update completed: {datetime.datetime.now().isoformat()}")
        except Exception as e:
            print(f"[CDN File List] file list update error: {e}")
        
        time.sleep(UPDATE_INTERVAL)


# --- FastAPI app creation ---
app = FastAPI()

# --- API endpoint definition ---
@app.post("/log") # POST method of /log path
async def receive_log(log_entry: LogEntry, background_tasks: BackgroundTasks): # bind LogEntry model에 자동으로 바인딩
    try:

        if log_entry.level == "SUCCESS":
            print(f"[{log_entry.timestamp}] [{log_entry.level.upper()}] {log_entry.message} (Found_URL: {log_entry.origin_url}) (Domain: {log_entry.domain})")
            background_tasks.add_task(
                process_reduction,
                log_entry.domain, "https://" + log_entry.domain + log_entry.origin_url, log_entry.filename_base + ".webp"
            )
        else:
            print(f"[{log_entry.timestamp}] [{log_entry.level.upper()}] {log_entry.message} (Missed_URL: {log_entry.origin_url}) (Domain: {log_entry.domain})")
            print(f"\nprocess_image {log_entry.domain} {log_entry.origin_url}\n")
            background_tasks.add_task(
                process_image,
                log_entry.domain, log_entry.origin_url, "cdn.ecarbon.kr", 
                90, log_entry.filename_base, log_entry.original_path_query
        )

        return {"status": "received", "message": "Log received and processing started."}

    except Exception as e:
        print(f"[SERVER ERROR] Error processing log request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing log request: {str(e)}"
        )

# --- server run ---
if __name__ == "__main__":
    HOST = "0.0.0.0" # all interfaces
    PORT = 5000      # port 5000

    print(f"Log monitoring server starting on http://{HOST}:{PORT}")
    print("Ensure firewall allows incoming connections on this port.")
    print("-----------------------------------------------------------")
    print("To run manually with auto-reload (for development):")
    print(f"uvicorn {__file__.split('/')[-1].replace('.py', '')}:app --host {HOST} --port {PORT} --reload")
    print("-----------------------------------------------------------")


    # init and update cdn file list threads
    init_thread = threading.Thread(target=init_cdn_file_list, daemon=True)
    init_thread.start()
    print("[CDN File List] initial file list creation thread started")


    # update cdn file list thread
    updater_thread = threading.Thread(target=update_cdn_file_list_periodically, daemon=True)
    updater_thread.start()
    print("[CDN File List] update cdn file list thread started")

    # Uvicorn server run
    uvicorn.run(app, host=HOST, port=PORT)