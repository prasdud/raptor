# LLM-Powered Mitigations Integration

## Overview

RAPTOR now uses **Cohere's LLM** to generate intelligent, context-aware security mitigations based on complete penetration test results. Instead of fixed/hardcoded recommendations, the system analyzes all scan data and produces tailored mitigation strategies.

## Architecture

### Flow Diagram

```
┌─────────────────┐
│  Recon Phase    │
│  (File Scan)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AI Analysis    │
│  (Sensitivity)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Attack Planning │
│  (AI Decision)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Build Master JSON              │
│  (recon + findings + attacks)   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  LLM Mitigation Generation      │ ◄── NEW STEP
│  (Cohere API)                   │
│  - Analyzes complete JSON       │
│  - Generates 8-12 mitigations   │
│  - Prioritizes by severity      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Report Gen     │
│  (PDF/LaTeX)    │
└─────────────────┘
```

### Components

1. **LLM Service** (`src/c2/scans/llm_service.py`)
   - Encapsulates Cohere API logic
   - Builds comprehensive prompts from scan data
   - Parses LLM responses into clean mitigation lists
   - Provides fallback mitigations if LLM fails

2. **Orchestrator Integration** (`src/c2/scans/orchestrator.py`)
   - New step 5.5: `_generate_llm_mitigations()`
   - Called after master JSON is built
   - Replaces static mitigations with LLM-generated ones
   - Gracefully falls back to hardcoded mitigations

3. **Settings** (`src/c2/c2/settings.py`)
   - `COHERE_API_KEY` configuration from environment variable

## Setup

### 1. Install Cohere SDK

```bash
cd /home/prasdud/playground/raptor
source venv/bin/activate  # if using virtual environment
pip install cohere==5.13.5
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 2. Get Cohere API Key

1. Sign up at https://dashboard.cohere.com/
2. Navigate to **API Keys** section
3. Create a new API key (free tier available)
4. Copy the key

### 3. Configure API Key

**Option A: Environment Variable (Recommended for VPS)**

```bash
# Add to ~/.bashrc or ~/.profile
export COHERE_API_KEY="your-api-key-here"

# Reload
source ~/.bashrc
```

**Option B: Django Settings (Development)**

Edit `src/c2/c2/settings.py`:

```python
# AI/LLM Configuration
import os
COHERE_API_KEY = os.environ.get('COHERE_API_KEY', 'your-api-key-here')
```

⚠️ **Never commit API keys to git!**

### 4. Verify Installation

```bash
cd src/c2
python manage.py shell
```

```python
from scans.llm_service import LLMMitigationService

# Test initialization
llm = LLMMitigationService()
print("✓ LLM Service initialized successfully!")

# Test mitigation generation
test_data = {
    "target_name": "test-server",
    "exec_summary": {"overall_risk": "High"},
    "recon_data": {"os_name": "Ubuntu", "is_admin": True, "open_ports": [22, 80, 443]},
    "findings": [{"name": "Open SSH", "severity": "Medium", "evidence": "Port 22 open"}],
}

mitigations = llm.generate_mitigations(test_data, max_tokens=500)
print(f"✓ Generated {len(mitigations)} mitigations")
for i, m in enumerate(mitigations, 1):
    print(f"{i}. {m}")
```

## Usage

### Automatic Integration

Once configured, LLM mitigations are **automatically generated** during the pipeline:

```bash
# Run a scan (payload or test)
python3 tests/test_payload.py

# Pipeline automatically:
# 1. Runs recon
# 2. Analyzes files (AI)
# 3. Plans attacks (AI)
# 4. Builds master JSON
# 5. Generates LLM mitigations ◄── NEW
# 6. Creates PDF report
```

You'll see this in the logs:

```
📋 Step 5: Building master report JSON...
   ✓ Master JSON created (15234 bytes)
🤖 Step 5.5: Generating AI mitigations (LLM)...
   ✓ Generated 10 AI-powered mitigations
📄 Step 6: Generating PDF report...
```

### Manual Testing

Test the LLM service directly:

```python
from scans.orchestrator import PipelineOrchestrator
from scans.models import Session

# Get latest session
session = Session.objects.latest('start_time')

# Create orchestrator
orch = PipelineOrchestrator(session)

# Load existing data (simulate)
orch.master_data = session.master_json

# Generate mitigations
mitigations = orch._generate_llm_mitigations()

# Print results
for i, m in enumerate(mitigations, 1):
    print(f"{i}. {m}")
```

## LLM Prompt Engineering

The prompt sent to Cohere includes:

- **Target system** (hostname, OS, admin status)
- **Risk level** (Low/Medium/High/Critical)
- **Open ports** (up to 15 ports)
- **Security findings** (top 10 with severity)
- **Sensitive files** (top 10 discovered)
- **AI attack vectors** (recommended exploits)

Example prompt:

```
Analyze the following penetration test results and provide specific, actionable security mitigations.

**Target System:** DESKTOP-ABC123
**Risk Level:** High
**Operating System:** Windows 10 21H2
**Administrative Access:** YES - Privileged access detected
**Open Ports:** 7 ports detected - 135, 139, 445, 3389, 5357, 49152, 49153

**Security Findings:**
- [High] SMB Exposed: Port 445 open with potential RCE vulnerability
- [Medium] RDP Accessible: Port 3389 exposed to internet
- [Medium] Admin User Detected: Current user has elevated privileges

**Sensitive Files Identified:**
- C:\Users\Admin\Documents\passwords.txt
- C:\Users\Admin\Desktop\credentials.xlsx
- C:\ProgramData\Company\api_keys.json

**AI-Recommended Attack Vectors:**
- lateral_movement: Move to other systems via SMB
- credential_theft: Extract credentials from sensitive files

Based on this penetration test data, provide **8-12 prioritized security mitigations**...
```

## Customization

### Adjust LLM Parameters

Edit `src/c2/scans/orchestrator.py`:

```python
def _generate_llm_mitigations(self):
    llm_service = LLMMitigationService()
    
    mitigations = llm_service.generate_mitigations(
        master_json=self.master_data,
        max_tokens=3000,      # More detailed mitigations
        temperature=0.5       # More focused/deterministic
    )
```

**Temperature Guide:**
- `0.0-0.3`: Very focused, deterministic (best for compliance)
- `0.4-0.7`: Balanced (recommended)
- `0.8-1.0`: Creative, diverse recommendations

### Change LLM Model

Edit `src/c2/scans/llm_service.py`:

```python
response = self.client.chat(
    message=prompt,
    model="command-r",  # Faster, cheaper
    # model="command-r-plus",  # Default, most capable
    # model="command-light",  # Fastest, simpler tasks
    ...
)
```

### Modify Prompt

Edit `_build_prompt()` in `llm_service.py` to:
- Add more context (CVEs, compliance requirements)
- Change focus (e.g., prioritize compliance over technical)
- Adjust tone (technical vs. executive)

## Fallback Behavior

If LLM fails (no API key, network error, rate limit), the system:

1. **Logs a warning** (doesn't crash)
2. **Uses hardcoded mitigations** from `_generate_mitigations()`
3. **Continues report generation** normally

Example fallback mitigations:
- Implement principle of least privilege
- Close unnecessary ports
- Encrypt sensitive files
- Deploy EDR solution
- Enable logging and monitoring

## Cost Considerations

### Cohere Pricing (as of 2024)

**Free Tier:**
- 100 API calls/month
- 1000 generations/month
- Good for testing and small deployments

**Production Tier:**
- Pay-as-you-go
- ~$1 per 1M input tokens
- ~$2 per 1M output tokens

### Estimated Cost per Report

- **Input tokens**: ~500-1000 (scan data)
- **Output tokens**: ~300-500 (mitigations)
- **Cost per report**: ~$0.001-0.003 (less than 1 cent)

For 1000 reports/month: **~$2-3/month**

## Deployment

### VPS Deployment

1. **Set environment variable on VPS:**

```bash
ssh user@your-vps

# Add to systemd service
sudo nano /etc/systemd/system/raptor.service
```

Add this under `[Service]`:

```ini
[Service]
Environment="COHERE_API_KEY=your-key-here"
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/path/to/venv/bin"
...
```

2. **Reload and restart:**

```bash
sudo systemctl daemon-reload
sudo systemctl restart raptor
```

3. **Verify:**

```bash
sudo journalctl -u raptor -f
# Should see: "✓ Generated X AI-powered mitigations"
```

### Docker Deployment

Add to `docker-compose.yml`:

```yaml
services:
  raptor:
    environment:
      - COHERE_API_KEY=${COHERE_API_KEY}
```

Then:

```bash
export COHERE_API_KEY="your-key"
docker-compose up -d
```

## Troubleshooting

### "COHERE_API_KEY not found"

**Symptom:** Warning in logs, fallback mitigations used

**Solution:**
```bash
# Check environment variable
echo $COHERE_API_KEY

# Set it
export COHERE_API_KEY="your-key"

# Verify in Django
cd src/c2
python manage.py shell
>>> from django.conf import settings
>>> print(settings.COHERE_API_KEY)
```

### "Import cohere could not be resolved"

**Symptom:** Import error when starting Django

**Solution:**
```bash
pip install cohere==5.13.5
pip install -r requirements.txt
```

### "Rate limit exceeded"

**Symptom:** API returns 429 error

**Solution:**
- Use free tier: Wait until next month
- Upgrade: Add payment method in Cohere dashboard
- Reduce calls: Cache mitigations for similar scans

### "Mitigations are too generic"

**Symptom:** LLM generates vague recommendations

**Solution:**
- Increase `max_tokens` (e.g., 3000)
- Lower `temperature` (e.g., 0.5)
- Enhance prompt with more specific examples
- Add domain-specific context (industry, compliance)

## Testing

### Unit Test

```bash
cd src/c2
python manage.py test scans.tests.TestLLMService
```

### Integration Test

```bash
# Run full pipeline
python3 tests/test_payload.py

# Check generated report
ls -lh src/c2/generated_reports/
```

### Manual Verification

1. Open generated PDF report
2. Navigate to "LLM Based Mitigations" section
3. Verify mitigations are:
   - Specific to your scan findings
   - Actionable (clear steps)
   - Prioritized (critical first)
   - Different from previous runs (not cached)

## Future Enhancements

- [ ] **Multi-model support** (OpenAI, Claude, Gemini)
- [ ] **Mitigation caching** (reduce API calls for similar scans)
- [ ] **Compliance mapping** (link mitigations to CIS/NIST controls)
- [ ] **Executive summary** (non-technical recommendations for C-suite)
- [ ] **Automated remediation scripts** (LLM generates bash/PowerShell)

## References

- [Cohere Documentation](https://docs.cohere.com/)
- [Cohere Python SDK](https://github.com/cohere-ai/cohere-python)
- [RAPTOR Architecture](./architecture.md)
