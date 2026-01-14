import requests
import os
import sys

BASE_URL = "http://localhost:8000"
PDF_PATH = os.path.join(os.path.dirname(__file__), "Remote_Work_policy.pdf")

def test_health():
    print(f"Testing Health at {BASE_URL}/health...")
    try:
        r = requests.get(f"{BASE_URL}/health")
        r.raise_for_status()
        data = r.json()
        if data["status"] == "healthy":
            print("✅ Health Check Passed")
            return True
        else:
            print(f"❌ Health Check Failed: {data}")
            return False
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False

def test_ingest():
    print(f"\nTesting Ingestion of {PDF_PATH}...")
    if not os.path.exists(PDF_PATH):
        print(f"❌ File not found: {PDF_PATH}")
        return False
        
    with open(PDF_PATH, "rb") as f:
        pdf_content = f.read()
        
    import base64
    base64_content = base64.b64encode(pdf_content).decode("utf-8")
    
    payload = {
        "filename": "Remote_Work_policy.pdf",
        "tag": "HR",
        "base64_content": base64_content,
        "uploaded_by": "tester"
    }
    
    # We need the API Key? 
    # The config says API_KEY is required.
    # We should grab it from docker-compose or .env or default.
    # The code relies on "Authorization: Bearer <API_KEY>" ?
    # Let's check gradio_app.py or backend main.py
    # Backend main.py likely enforces it.
    
    headers = {"Authorization": "Bearer dev-secret-key-12345"} 
    
    try:
        r = requests.post(f"{BASE_URL}/ingest", json=payload, headers=headers)
        if r.status_code == 201:
            print("✅ Ingestion Passed")
            return True
        else:
            # If it already exists, that's fine too for persistence check
            if "already exists" in r.text:
                 print("✅ Ingestion Passed (Already Exists)")
                 return True
            print(f"❌ Ingestion Failed: {r.status_code} - {r.text}")
            return False
    except Exception as e:
         print(f"❌ Ingestion Error: {e}")
         return False

def test_retrieve():
    print("\nTesting Retrieval...")
    headers = {"Authorization": "Bearer dev-secret-key-12345"}
    payload = {
        "query": "Remote work",
        "tag": "HR",
        "top_k": 3
    }
    try:
        r = requests.post(f"{BASE_URL}/retrieve", json=payload, headers=headers)
        if r.status_code == 200:
            data = r.json()
            if "results" in data:
                print(f"✅ Retrieval Passed. Found {len(data['results'])} results.")
                return True
        print(f"❌ Retrieval Failed: {r.status_code} - {r.text}")
        return False
    except Exception as e:
        print(f"❌ Retrieval Error: {e}")
        return False

def test_chat():
    print("\nTesting Chat...")
    headers = {"Authorization": "Bearer dev-secret-key-12345"}
    payload = {
        "query": "Remote work policy",
        "tag": "HR",
        "top_k": 3
    }
    try:
        r = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
        if r.status_code == 200:
            data = r.json()
            if "answer" in data:
                print(f"✅ Chat Passed. Answer: {data['answer'][:50]}...")
                return True
        print(f"❌ Chat Failed: {r.status_code} - {r.text}")
        return False
    except Exception as e:
        print(f"❌ Chat Error: {e}")
        return False

if __name__ == "__main__":
    if test_health():
        ingest_ok = test_ingest()
        if ingest_ok:
            test_retrieve()
            test_chat()
