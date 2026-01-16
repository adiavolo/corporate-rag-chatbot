import requests
import base64
import os
import sys

API_URL = "http://localhost:8000"
FILE_PATH = "tests/test_doc.pdf"

def verify_ingest():
    if not os.path.exists(FILE_PATH):
        print(f"Error: {FILE_PATH} not found. Run generate script first.")
        sys.exit(1)

    with open(FILE_PATH, "rb") as f:
        content = f.read()
    
    b64_content = base64.b64encode(content).decode('utf-8')
    
    payload = {
        "filename": "test_doc.pdf",
        "tag": "HR",
        "base64_content": b64_content,
        "uploaded_by": "test_script"
    }
    
    headers = {
        "Authorization": "Bearer dev-secret-key-12345"
    }
    
    print(f"Sending request to {API_URL}/ingest...")
    try:
        response = requests.post(f"{API_URL}/ingest", json=payload, headers=headers)
        
        if response.status_code == 201:
            print("✅ Ingestion Successful!")
            print(response.json())
        else:
            print(f"❌ Ingestion Failed: {response.status_code}")
            print(response.text)
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_ingest()
