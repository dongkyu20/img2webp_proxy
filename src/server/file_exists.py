import os
from google.cloud import storage
from google.api_core import exceptions # 예외 처리를 위해 임포트

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "woven-province-411903-b1b12d94b3ac.json"


def list_blobs_in_bucket(bucket_name, output_file="cdn_file_list.txt", timeout=None):
    """Print the list of files in the specified Google Cloud Storage bucket and save it to a text file."""
    
    storage_client = storage.Client()
    storage_client._http.timeout = timeout if timeout else None

    try:
        blobs = storage_client.list_blobs(bucket_name)

        print(f"'{bucket_name}' bucket file list:")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            found_files = False
            for blob in blobs:
                blob_name = blob.name
                blob_size = blob.size
                size_kb = blob_size / 1024
                size_mb = size_kb / 1024
                
                if size_mb >= 1:
                    size_display = f"{size_mb:.2f} MB"
                else:
                    size_display = f"{size_kb:.2f} KB"
                
                print(f"- {blob_name} ({size_display})")
                f.write(f"{blob_name}\t{blob_size} bytes\n")
                found_files = True

            if not found_files:
                print("  (file not found in bucket)")
                f.write("(file not found in bucket)\n")

    except exceptions.NotFound:
        print(f"Error: Bucket '{bucket_name}' not found.")
    except exceptions.Forbidden:
        print(f"Error: Access to bucket '{bucket_name}' forbidden. Check IAM permissions.")
    except Exception as e:
        print(f"Unknown error: {e}")