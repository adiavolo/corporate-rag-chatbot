import json
import requests
import sys
import os

# Configuration
API_URL = "http://localhost:8000/chat"
API_KEY = "dev-secret-key-12345"  # From .env
TEST_FILE = "tests/hr_questions.json"

def run_tests():
    # Load questions
    try:
        with open(TEST_FILE, "r") as f:
            questions = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {TEST_FILE} not found.")
        sys.exit(1)

    print(f"🚀 Starting Test Run: {len(questions)} questions")
    print("-" * 60)

    passed = 0
    failed = 0
    results = []

    for q in questions:
        print(f"Running {q['id']}: {q['question'][:50]}...", end="", flush=True)
        
        payload = {
            "query": q["question"],
            "tag": "HR"
        }
        headers = {
            "Authorization": f"Bearer {API_KEY}"
        }

        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            answer = data["answer"]
            sources = data["sources"]
            
            # Evaluation Logic
            is_pass = True
            reasons = []

            # 1. Check "Must Include" (Keywords)
            if "must_include" in q:
                for phrase in q["must_include"]:
                    if phrase.lower() not in answer.lower():
                        is_pass = False
                        reasons.append(f"Missing keyword: '{phrase}'")

            # 2. Check "Must Refuse" (Refusal)
            if q.get("must_refuse", False):
                if "I don't have enough information" not in answer:
                    is_pass = False
                    reasons.append("Did not refuse answer as expected")

            # 3. Check Clarification
            if q.get("must_ask_clarification", False):
                # Heuristic: Short answer or question mark or specific phrase?
                # For now, let's just check if it's not a confident statement or asks for info
                pass # Skip automated check for ambiguity for now, user to verify

            if is_pass:
                print(" ✅ PASS")
                passed += 1
            else:
                print(" ❌ FAIL")
                print(f"   -> Expectation: {reasons}")
                print(f"   -> Actual Answer: {answer}")
                failed += 1

        except Exception as e:
            print(" 💥 ERROR")
            print(f"   -> {e}")
            failed += 1

    print("-" * 60)
    print(f"🏁 Test Complete. Passed: {passed}/{len(questions)} ({passed/len(questions)*100:.1f}%)")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
