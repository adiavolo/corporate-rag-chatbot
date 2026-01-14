import json
import requests
import sys
import os
from datetime import datetime

API_URL = "http://localhost:8000/chat"
API_KEY = "dev-secret-key-12345"
TEST_FILE = "tests/multi_domain_questions.json"
REPORT_FILE = "tests/latest_report.md"

def run_tests():
    try:
        with open(TEST_FILE, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load test file: {e}")
        sys.exit(1)

    # Open Report File
    report = open(REPORT_FILE, "w", encoding="utf-8")
    transcript = open("tests/test_transcript.txt", "w", encoding="utf-8")

    def log(msg, file_only=False):
        if not file_only:
            print(msg)
        report.write(msg + "\n")

    def log_trans(msg):
        transcript.write(msg + "\n")

    log(f"# 🧪 RAG Test Report")
    log_trans(f"TEST TRANSCRIPT - {datetime.now()}\n==================================================\n")
    log(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"**Test File:** `{TEST_FILE}`\n")
    
    log("| Question | Tag | Domain | Result | Check |")
    log("| :--- | :--- | :--- | :--- | :--- |")

    results = {
        "HR": {"total": 0, "correct": 0},
        "Legal": {"total": 0, "correct": 0},
        "Cross": {"total": 0, "correct": 0},
        "Hallucination": {"total": 0, "failed": 0} 
    }

    # --- Helper to Test a Question ---
    def test_question(q, override_tag=None):
        tag = override_tag or q.get("tag")
        payload = {"query": q["question"], "tag": tag}
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        try:
            resp = requests.post(API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            ans = resp.json()
            answer_text = ans["answer"].lower()
            
            status = "Correct"
            details = ""
            
            # Check Refusal
            if q.get("must_refuse"):
                if "i don't have enough information" in answer_text:
                    status = "Correct"
                    details = "Refused as expected"
                else:
                    status = "Fail: Hallucinated"
                    details = f"Generated answer: {ans['answer'][:30]}..."
            else:
                # Check Concepts
                allowed = q.get("expected_concepts", [])
                forbidden = q.get("forbidden_concepts", [])
                
                has_allowed = any(c.lower() in answer_text for c in allowed)
                has_forbidden = any(c.lower() in answer_text for c in forbidden)
                
                if "i don't have enough information" in answer_text:
                    # For Cross-Domain, Refusal IS often correct behavior if siloed, but strict test counts as 'Refused'
                    status = "Refused" 
                    details = "Bot returned 'Not enough info'"
                elif has_forbidden:
                    status = "Wrong Domain"
                    matched = [c for c in forbidden if c.lower() in answer_text]
                    details = f"Found forbidden terms: {matched}"
                elif not has_allowed:
                    status = "Partial/Vague"
                    details = "Missing expected key concepts"
                else:
                    details = "Found expected concepts"
            
            # Log Transcript
            log_trans(f"TAG: {tag}")
            log_trans(f"Q:   {q['question']}")
            log_trans(f"A:   {ans['answer']}")
            log_trans(f"RES: {status} ({details})")
            log_trans("-" * 40)
            
            return status, details

        except Exception as e:
            log_trans(f"ERROR: {e}")
            return f"Error: {e}", str(e)

    # --- Run Groups ---

    for q in data["group_a"]:
        res, det = test_question(q)
        results["HR"]["total"] += 1
        if res == "Correct": results["HR"]["correct"] += 1
        emoji = "✅" if res == "Correct" else "❌"
        log(f"| {q['question'][:40]}... | {q['tag']} | HR | {res} | {emoji} {det} |")

    for q in data["group_b"]:
        res, det = test_question(q)
        results["Legal"]["total"] += 1
        if res == "Correct": results["Legal"]["correct"] += 1
        emoji = "✅" if res == "Correct" else "❌"
        log(f"| {q['question'][:40]}... | {q['tag']} | Legal | {res} | {emoji} {det} |")

    for q in data["group_c"]:
        target_domain = "HR" if q["id"].endswith("HR") else "Legal"
        res, det = test_question(q)
        results["Cross"]["total"] += 1
        # Loosen strictness: "Refused" is acceptable for Cross Domain isolation
        if res == "Correct": 
            results["Cross"]["correct"] += 1
            emoji = "✅"
        elif res == "Refused":
            # Count refusal as isolation success?
            # For strict reporting, let's keep it separate or note it.
            # Let's count it as correct for Isolation if the goal is isolation.
             emoji = "⚠️"
        else:
            emoji = "❌"
            
        log(f"| {q['question'][:40]}... | {q['tag']} | {target_domain} | {res} | {emoji} {det} |")

    for q in data["group_d"]:
        for tag in q["tags"]:
            res, det = test_question(q, override_tag=tag)
            results["Hallucination"]["total"] += 1
            if res != "Correct": results["Hallucination"]["failed"] += 1
            emoji = "✅" if res == "Correct" else "❌"
            log(f"| {q['question'][:40]}... | {tag} | None | {res} | {emoji} {det} |")

    # --- Summary ---
    hr_acc = results["HR"]["correct"] / results["HR"]["total"] if results["HR"]["total"] else 0
    legal_acc = results["Legal"]["correct"] / results["Legal"]["total"] if results["Legal"]["total"] else 0
    cross_acc = results["Cross"]["correct"] / results["Cross"]["total"] if results["Cross"]["total"] else 0
    hall_fail = results["Hallucination"]["failed"]
    
    log("\n## 📊 Summary Statistics")
    log(f"- **HR Accuracy**: {results['HR']['correct']}/{results['HR']['total']} ({hr_acc:.0%})")
    log(f"- **Legal Accuracy**: {results['Legal']['correct']}/{results['Legal']['total']} ({legal_acc:.0%})")
    log(f"- **Domain Isolation (Strict)**: {results['Cross']['correct']}/{results['Cross']['total']} ({cross_acc:.0%})")
    log(f"- **Hallucinations**: {hall_fail}/{results['Hallucination']['total']}")

    report.close()
    print(f"\n✅ Report generated at: {os.path.abspath(REPORT_FILE)}")

if __name__ == "__main__":
    run_tests()
