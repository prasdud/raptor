# RAPTOR LLM Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAPTOR C2 Server                        │
│                       (Django Application)                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP POST
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                         │
│                   (scans/orchestrator.py)                        │
└─────────────────────────────────────────────────────────────────┘
                                │
            ┌───────────────────┴───────────────────┐
            │                                       │
            ▼                                       ▼
┌──────────────────────┐                 ┌──────────────────────┐
│   Step 1: Recon      │                 │  Step 2: File Enum   │
│   - Port scan        │                 │  - Discover files    │
│   - OS detection     │                 │  - Extract metadata  │
│   - Service enum     │                 │                      │
└──────────────────────┘                 └──────────────────────┘
            │                                       │
            └───────────────────┬───────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: File Sensitivity AI                                    │
│  - LightGBM classifier                                          │
│  - Predicts: High/Medium/Low sensitivity                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Attack Decision AI                                     │
│  - Random Forest classifier                                     │
│  - Recommends: data_exfil, priv_esc, network_scan, etc.        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Build Master JSON                                      │
│  {                                                              │
│    "target_name": "...",                                        │
│    "recon_data": {...},                                         │
│    "findings": [...],                                           │
│    "attacks": [...],                                            │
│    "mitigations": []  ← Empty initially                         │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5.5: LLM Mitigation Generation ★ NEW ★                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  LLMMitigationService                                     │ │
│  │  (scans/llm_service.py)                                   │ │
│  │                                                           │ │
│  │  1. Build prompt from master JSON:                       │ │
│  │     - Target info (OS, hostname, risk)                   │ │
│  │     - Findings (top 10 with severity)                    │ │
│  │     - Open ports (up to 15)                              │ │
│  │     - Sensitive files (top 10)                           │ │
│  │     - Attack vectors (AI recommendations)                │ │
│  │                                                           │ │
│  │  2. Call Cohere API:                                     │ │
│  │     POST https://api.cohere.ai/v1/chat                   │ │
│  │     {                                                     │ │
│  │       "model": "command-r-plus",                         │ │
│  │       "message": "<detailed prompt>",                    │ │
│  │       "preamble": "You are a cybersec expert...",        │ │
│  │       "max_tokens": 2000,                                │ │
│  │       "temperature": 0.7                                 │ │
│  │     }                                                     │ │
│  │                                                           │ │
│  │  3. Parse response:                                      │ │
│  │     - Extract numbered list                              │ │
│  │     - Clean formatting (remove **, numbers, bullets)     │ │
│  │     - Return 8-12 mitigations                            │ │
│  │                                                           │ │
│  │  4. Fallback on error:                                   │ │
│  │     - API key missing → use hardcoded mitigations        │ │
│  │     - Network error → use hardcoded mitigations          │ │
│  │     - Rate limit → use hardcoded mitigations             │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Master JSON Updated:                                           │
│  {                                                              │
│    "target_name": "PROD-WEB-01",                                │
│    "mitigations": [                                             │
│      "Restrict MySQL port 3306 to internal network only",       │
│      "Enable authentication on Jenkins CI/CD pipeline",         │
│      "Rotate exposed SSH keys and implement cert-based auth",   │
│      "Migrate credentials to secrets manager (Vault/AWS)",      │
│      "Deploy WAF to detect SQL injection attempts",             │
│      "Implement network segmentation for database tier",        │
│      "Enable comprehensive audit logging to SIEM",              │
│      "Schedule security training on secrets management"         │
│    ]                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 6: Generate PDF Report                                    │
│  - Render Jinja2 template                                       │
│  - Compile LaTeX → PDF                                          │
│  - Include "LLM Based Mitigations" section                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 7: Update Session                                         │
│  - Status: complete                                             │
│  - Save master_json (with LLM mitigations)                      │
│  - Save report path                                             │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Detail

### Prompt Construction

```python
# Input: master_data from orchestrator
{
  "target_name": "PROD-WEB-01",
  "exec_summary": {
    "overall_risk": "High",
    "open_ports_list": ["22 - SSH", "3306 - MySQL"],
    "sensitive_data_list": ["/var/www/config/database.yml"]
  },
  "findings": [
    {
      "name": "MySQL Exposed",
      "severity": "Critical",
      "evidence": "Port 3306 open to internet"
    }
  ]
}

# ↓ Transform to prompt ↓

"""
Analyze the following penetration test results and provide specific, 
actionable security mitigations.

**Target System:** PROD-WEB-01
**Risk Level:** High
**Operating System:** Ubuntu 22.04 LTS
**Administrative Access:** NO
**Open Ports:** 5 ports detected - 22, 80, 443, 3306, 8080

**Security Findings:**
- [Critical] MySQL Exposed: Port 3306 open to internet
- [High] Jenkins Unauthenticated: Port 8080 allows anonymous access
- [High] SSH Keys Discovered: Private key in /home/admin/.ssh/
- [Medium] No Endpoint Protection: No AV/EDR detected

**Sensitive Files Identified:**
- /var/www/config/database.yml
- /home/admin/.ssh/id_rsa
- /opt/app/secrets.json

**AI-Recommended Attack Vectors:**
- database_access: Attempt direct MySQL connection via port 3306
- jenkins_exploit: Inject malicious pipeline for RCE

Based on this data, provide 8-12 prioritized security mitigations...
"""
```

### LLM Response Parsing

```python
# Raw LLM response (with markdown)
"""
**1. Immediately restrict MySQL port 3306 to internal network only**

Use firewall rules (iptables or cloud security groups) to limit access.

**2. Enable authentication on Jenkins (port 8080)**

Implement role-based access control for CI/CD pipeline access.

**3. Rotate exposed SSH keys**

Implement SSH certificate-based authentication with short-lived credentials.
...
"""

# ↓ Parse & clean ↓

[
  "Immediately restrict MySQL port 3306 to internal network only using firewall rules (iptables or cloud security groups)",
  "Enable authentication on Jenkins (port 8080) and implement role-based access control for CI/CD pipeline access",
  "Rotate exposed SSH keys and implement SSH certificate-based authentication with short-lived credentials",
  ...
]
```

## Configuration Flow

```
┌─────────────────────────┐
│  Environment Variable   │
│  COHERE_API_KEY="..."   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Django Settings        │
│  (c2/settings.py)       │
│                         │
│  COHERE_API_KEY =       │
│    os.getenv(...)       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  LLM Service Init       │
│  (llm_service.py)       │
│                         │
│  api_key = getattr(     │
│    settings,            │
│    'COHERE_API_KEY'     │
│  )                      │
│                         │
│  if not api_key:        │
│    raise ValueError     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Cohere Client          │
│                         │
│  client = cohere.Client(│
│    api_key=api_key      │
│  )                      │
└─────────────────────────┘
```

## Error Handling

```
┌─────────────────────────────────────┐
│  _generate_llm_mitigations()        │
└───────────┬─────────────────────────┘
            │
            ▼
     ┌──────────────┐
     │ Try: Init    │
     │ LLM Service  │
     └──────┬───────┘
            │
    ┌───────┴───────┐
    │               │
    ▼               ▼
┌────────┐    ┌──────────────┐
│Success │    │ValueError    │
│        │    │(No API key)  │
└───┬────┘    └──────┬───────┘
    │                │
    │                └─→ Log warning
    │                    Return None
    │                    Use fallback
    ▼
┌─────────────────┐
│ Try: Generate   │
│ mitigations     │
└────────┬────────┘
         │
   ┌─────┴─────┐
   │           │
   ▼           ▼
┌────────┐ ┌─────────────┐
│Success │ │Exception    │
│        │ │(API error)  │
└───┬────┘ └──────┬──────┘
    │             │
    │             └─→ Log error
    │                 Return None
    │                 Use fallback
    ▼
┌──────────────────────┐
│ Return mitigations   │
│ (8-12 items)         │
└──────────────────────┘
```

## Cost Analysis

```
Single Report Generation
│
├─ Input Tokens: ~500-1000
│  ├─ Target info: 50 tokens
│  ├─ Findings: 200-400 tokens
│  ├─ Recon data: 150-300 tokens
│  └─ Prompt template: 100-150 tokens
│
├─ Output Tokens: ~300-500
│  └─ 8-12 mitigations @ 30-40 tokens each
│
└─ Cost per Report
   ├─ Input: $0.0005-0.001 (@ $1/1M tokens)
   ├─ Output: $0.0006-0.001 (@ $2/1M tokens)
   └─ Total: ~$0.001-0.003 per report

Monthly Costs (1000 reports)
│
├─ Free Tier: 100 calls/month → $0
├─ Paid Tier: 1000 calls/month → $2-3/month
└─ Enterprise: 10,000 calls/month → $20-30/month
```

## Integration Points

### New Components
1. **LLM Service Module** (`llm_service.py`)
   - Cohere API client wrapper
   - Prompt engineering
   - Response parsing
   - Fallback logic

2. **Settings Configuration** (`settings.py`)
   - API key management
   - Environment variable loading

3. **Orchestrator Enhancement** (`orchestrator.py`)
   - New pipeline step 5.5
   - LLM service invocation
   - Mitigation replacement

### Existing Components (Unchanged)
1. **Report Template** (Jinja2/LaTeX)
   - Still iterates `mitigations` list
   - No changes to rendering logic

2. **API Endpoints** (Django views)
   - No new endpoints required
   - Existing `/api/submit_scan/` unchanged

3. **Database Schema**
   - No migrations needed
   - `master_json` field stores LLM output

## Security Considerations

```
┌─────────────────────────────────────────────────┐
│  Security Best Practices                        │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. API Key Storage                             │
│     ✓ Use environment variables                 │
│     ✗ Never commit to git                       │
│     ✓ Rotate keys regularly                     │
│                                                 │
│  2. Data Transmission                           │
│     ✓ HTTPS to Cohere (encrypted)               │
│     ✓ No PII in prompts (hostnames only)        │
│     ✓ Scan data stays on your server            │
│                                                 │
│  3. Rate Limiting                               │
│     ✓ Cohere enforces limits (100/month free)   │
│     ✓ Graceful degradation (fallback)           │
│     ✓ No retry storms (fail once)               │
│                                                 │
│  4. Input Validation                            │
│     ✓ Sanitize master_json before prompt        │
│     ✓ Limit prompt size (max 10 findings)       │
│     ✓ Validate LLM response format              │
│                                                 │
│  5. Output Validation                           │
│     ✓ Parse mitigations into clean list         │
│     ✓ Cap at 12 items                           │
│     ✓ Strip markdown/formatting                 │
│                                                 │
└─────────────────────────────────────────────────┘
```
