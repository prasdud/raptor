# LLM Mitigations - Quick Start Guide

## What Changed

RAPTOR now uses **Cohere's AI** to generate intelligent security mitigations instead of hardcoded recommendations. The LLM analyzes your complete penetration test data and produces tailored mitigation strategies.

## Installation (5 minutes)

### 1. Install Dependencies

```bash
cd /home/prasdud/playground/raptor
pip install cohere==5.13.5
```

Or use the automated script:

```bash
./setup_llm.sh
```

### 2. Get API Key

1. Visit https://dashboard.cohere.com/
2. Sign up (free tier available)
3. Go to **API Keys** → **Create New Key**
4. Copy your key

### 3. Set API Key

```bash
# Option 1: Environment variable (recommended)
export COHERE_API_KEY="your-api-key-here"

# Make it permanent (add to ~/.bashrc)
echo 'export COHERE_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# Option 2: Django settings (development only)
# Edit src/c2/c2/settings.py and hardcode the key
```

### 4. Test It

```bash
# Quick test
python3 tests/test_llm_mitigations.py

# Full integration test
python3 tests/test_payload.py
```

## How It Works

### Before (Static Mitigations)

```python
# orchestrator.py - OLD
def _generate_mitigations(self, recon_data, sensitive_files):
    mitigations = [
        "Implement principle of least privilege",
        "Close unnecessary ports",
        "Encrypt sensitive files",
        # ... same for every scan
    ]
    return mitigations
```

### After (AI-Powered Mitigations)

```python
# orchestrator.py - NEW
def _generate_llm_mitigations(self):
    # Send complete scan data to Cohere
    llm_service = LLMMitigationService()
    mitigations = llm_service.generate_mitigations(
        master_json=self.master_data  # All recon, findings, attacks
    )
    return mitigations  # Custom for this specific scan
```

### Pipeline Flow

```
Recon → AI Analysis → Attack Planning → Build JSON
                                           ↓
                                    LLM Mitigation ← NEW STEP
                                           ↓
                                    Generate Report (PDF)
```

## Example Output

### Input (Scan Data)
```json
{
  "target": "PROD-WEB-01",
  "risk_level": "High",
  "findings": [
    "MySQL port 3306 exposed to internet",
    "Jenkins unauthenticated access on 8080",
    "SSH private keys in /home/admin/.ssh/",
    "Database credentials in plaintext"
  ]
}
```

### Output (AI Mitigations)
```
1. Immediately restrict MySQL port 3306 to internal network only using 
   firewall rules (iptables or cloud security groups)

2. Enable authentication on Jenkins (port 8080) and implement role-based 
   access control for CI/CD pipeline access

3. Rotate exposed SSH keys and implement SSH certificate-based authentication 
   with short-lived credentials

4. Migrate database credentials to a secrets management solution like 
   HashiCorp Vault or AWS Secrets Manager

5. Deploy a Web Application Firewall (WAF) in front of nginx to detect 
   SQL injection attempts targeting the MySQL backend

6. Implement network segmentation to isolate the database server in a 
   separate VLAN with strict access controls

7. Enable audit logging for all database access and forward logs to a 
   centralized SIEM for anomaly detection

8. Schedule immediate security awareness training focusing on secrets 
   management and secure CI/CD practices
```

Notice how it's **specific to the findings** (MySQL, Jenkins, SSH keys) rather than generic advice!

## Configuration Options

### Adjust LLM Behavior

Edit `src/c2/scans/orchestrator.py`:

```python
mitigations = llm_service.generate_mitigations(
    master_json=self.master_data,
    max_tokens=3000,     # More detailed (default: 2000)
    temperature=0.5      # More focused (default: 0.7)
)
```

**Temperature Guide:**
- `0.0-0.3`: Deterministic, conservative (good for compliance)
- `0.4-0.7`: Balanced (recommended)
- `0.8-1.0`: Creative, diverse (good for red team exercises)

### Change Model

Edit `src/c2/scans/llm_service.py`:

```python
response = self.client.chat(
    model="command-r-plus",  # Most capable (default)
    # model="command-r",     # Faster, cheaper
    # model="command-light", # Fastest
)
```

## Cost

### Free Tier
- **100 API calls/month** (plenty for testing)
- **1000 generations/month**

### Production Pricing
- **~$0.001 per report** (less than 1 cent!)
- **1000 reports/month = $2-3/month**

Way cheaper than hiring a consultant 😉

## Deployment

### Local Development
```bash
export COHERE_API_KEY="your-key"
python3 src/c2/manage.py runserver
```

### VPS Production

Edit systemd service:
```bash
sudo nano /etc/systemd/system/raptor.service
```

Add under `[Service]`:
```ini
Environment="COHERE_API_KEY=your-key-here"
```

Restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart raptor
```

Verify in logs:
```bash
sudo journalctl -u raptor -f
# Look for: "✓ Generated X AI-powered mitigations"
```

## Troubleshooting

### "COHERE_API_KEY not found"
```bash
# Check if set
echo $COHERE_API_KEY

# Set it
export COHERE_API_KEY="your-key"

# Verify Django can see it
cd src/c2
python manage.py shell
>>> from django.conf import settings
>>> print(settings.COHERE_API_KEY)
```

### "Import cohere could not be resolved"
```bash
pip install cohere==5.13.5
```

### Mitigations are generic/boring
- Increase `max_tokens` to 3000
- Lower `temperature` to 0.5
- Check that scan has specific findings (not all "N/A")

### API rate limit exceeded
- Free tier: 100 calls/month - wait or upgrade
- Paid tier: Add payment method in dashboard

## Files Changed

### New Files
- `src/c2/scans/llm_service.py` - LLM integration logic
- `docs/LLM_MITIGATIONS.md` - Full documentation
- `tests/test_llm_mitigations.py` - Integration test
- `setup_llm.sh` - Automated setup script

### Modified Files
- `requirements.txt` - Added `cohere==5.13.5`
- `src/c2/c2/settings.py` - Added `COHERE_API_KEY` config
- `src/c2/scans/orchestrator.py` - Integrated LLM service

### Unchanged
- Report template (still renders mitigations the same way)
- API endpoints (no breaking changes)
- Database schema (no migrations needed)

## What If I Don't Want LLM?

**It's optional!** If you don't set `COHERE_API_KEY`:

1. System logs a warning
2. Uses original hardcoded mitigations
3. Everything else works normally

To disable completely, just don't run `setup_llm.sh`.

## Next Steps

1. **Test locally:**
   ```bash
   export COHERE_API_KEY="your-key"
   python3 tests/test_llm_mitigations.py
   ```

2. **Run full pipeline:**
   ```bash
   python3 tests/test_payload.py
   ```

3. **Check report:**
   ```bash
   ls -lh src/c2/generated_reports/
   # Open the PDF and look at "LLM Based Mitigations" section
   ```

4. **Deploy to VPS:**
   ```bash
   git add .
   git commit -m "Add LLM-powered mitigations"
   git push
   
   # On VPS:
   cd ~/services/raptor
   git pull
   pip install cohere==5.13.5
   sudo nano /etc/systemd/system/raptor.service  # Add API key
   sudo systemctl daemon-reload
   sudo systemctl restart raptor
   ```

## Support

- **Full docs:** `docs/LLM_MITIGATIONS.md`
- **Cohere docs:** https://docs.cohere.com/
- **Test script:** `tests/test_llm_mitigations.py`

---

**TL;DR:** Install Cohere, set API key, get smarter mitigations! 🚀
