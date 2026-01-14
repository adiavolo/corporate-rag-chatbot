# 🧪 RAG Test Report
**Date:** 2026-01-12 16:49:38
**Test File:** `tests/multi_domain_questions.json`

| Question | Tag | Domain | Result | Check |
| :--- | :--- | :--- | :--- | :--- |
| What is the probation period for new emp... | HR | HR | Refused | ❌ Bot returned 'Not enough info' |
| How many days of annual leave do full-ti... | HR | HR | Correct | ✅ Found expected concepts |
| What is the notice period for a confirme... | HR | HR | Correct | ✅ Found expected concepts |
| How is maternity leave handled?... | HR | HR | Correct | ✅ Found expected concepts |
| Who approves leave requests?... | HR | HR | Refused | ❌ Bot returned 'Not enough info' |
| How are working hours tracked?... | HR | HR | Correct | ✅ Found expected concepts |
| What happens after probation?... | HR | HR | Correct | ✅ Found expected concepts |
| What is bereavement leave?... | HR | HR | Correct | ✅ Found expected concepts |
| What is the payroll cycle?... | HR | HR | Correct | ✅ Found expected concepts |
| What happens during exit and offboarding... | HR | HR | Correct | ✅ Found expected concepts |
| What is a legal hold?... | Legal | Legal | Correct | ✅ Found expected concepts |
| Who is allowed to sign contracts?... | Legal | Legal | Correct | ✅ Found expected concepts |
| What happens if someone violates an NDA?... | Legal | Legal | Correct | ✅ Found expected concepts |
| How should legal disputes be handled?... | Legal | Legal | Correct | ✅ Found expected concepts |
| What is document retention?... | Legal | Legal | Partial/Vague | ❌ Missing expected key concepts |
| What happens if records are destroyed un... | Legal | Legal | Correct | ✅ Found expected concepts |
| Who handles lawsuits?... | Legal | Legal | Correct | ✅ Found expected concepts |
| How do you report legal violations?... | Legal | Legal | Correct | ✅ Found expected concepts |
| What are whistleblower protections?... | Legal | Legal | Refused | ❌ Bot returned 'Not enough info' |
| What happens to intellectual property af... | Legal | Legal | Correct | ✅ Found expected concepts |
| What happens when I leave the company?... | HR | HR | Correct | ✅ Found expected concepts |
| What happens when I leave the company?... | Legal | Legal | Refused | ⚠️ Bot returned 'Not enough info' |
| Confidential information... | HR | HR | Partial/Vague | ❌ Missing expected key concepts |
| Confidential information... | Legal | Legal | Partial/Vague | ❌ Missing expected key concepts |
| Agreements... | HR | HR | Refused | ⚠️ Bot returned 'Not enough info' |
| Agreements... | Legal | Legal | Partial/Vague | ❌ Missing expected key concepts |
| Disciplinary actions... | HR | HR | Correct | ✅ Found expected concepts |
| Disciplinary actions... | Legal | Legal | Correct | ✅ Found expected concepts |
| Data misuse... | HR | HR | Partial/Vague | ❌ Missing expected key concepts |
| Data misuse... | Legal | Legal | Refused | ⚠️ Bot returned 'Not enough info' |
| What stock options do employees get?... | HR | None | Correct | ✅ Refused as expected |
| What stock options do employees get?... | Legal | None | Correct | ✅ Refused as expected |
| Who is the CEO?... | HR | None | Correct | ✅ Refused as expected |
| Who is the CEO?... | Legal | None | Fail: Hallucinated | ❌ Generated answer: The Chief Executive Officer (C... |
| What is the companyâ€™s revenue?... | HR | None | Correct | ✅ Refused as expected |
| What is the companyâ€™s revenue?... | Legal | None | Correct | ✅ Refused as expected |
| What cloud provider does Aurora use?... | HR | None | Correct | ✅ Refused as expected |
| What cloud provider does Aurora use?... | Legal | None | Correct | ✅ Refused as expected |
| What programming languages does the comp... | HR | None | Correct | ✅ Refused as expected |
| What programming languages does the comp... | Legal | None | Correct | ✅ Refused as expected |

## 📊 Summary Statistics
- **HR Accuracy**: 8/10 (80%)
- **Legal Accuracy**: 8/10 (80%)
- **Domain Isolation (Strict)**: 3/10 (30%)
- **Hallucinations**: 1/10
