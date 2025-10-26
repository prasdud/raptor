# 🚀 RAPTOR: Red Team AI-Powered Penetration Testing Simulator# Red Team AI Malware Simulator - RAPTOR



**Status:** ✅ Fully Operational | **Version:** 2.0 Enhanced  ## Overview

An AI-driven penetration testing framework for educational purposes and security research.

The **Red Team AI Malware Simulator** is a controlled simulation framework designed for cybersecurity professionals to test and study malware behaviors in a safe and isolated environment. It emulates advanced attack techniques and decision-making logic of real-world malware, allowing red teamers and security researchers to analyze attack strategies, system vulnerabilities, and defense mechanisms.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

![Django](https://img.shields.io/badge/django-5.2.5-green.svg)This project combines **AI-driven intelligence** with traditional malware simulation, providing insights into adaptive malware behavior and response strategies.

![Tests](https://img.shields.io/badge/tests-33%2F33%20passing-brightgreen.svg)

![License](https://img.shields.io/badge/license-Educational-orange.svg)---



---## Key Features



## 🎯 What is RAPTOR?### 1. AI-Powered Decision Making

- **Evasion AI:** Detects sandboxing, virtual machines, and monitoring tools to avoid detection.

RAPTOR is a complete Command & Control (C2) framework that demonstrates how AI can be integrated into penetration testing workflows. It features **automated reconnaissance**, **AI-based decision-making** for attack planning, **intelligent file sensitivity analysis**, and **automated report generation**.- **Recon Prioritization AI:** Scores and ranks discovered system information to focus on high-value targets.

- **Attack Decision AI:** Determines the optimal sequence of attack actions based on system environment and previous findings.

### ✨ Key Features

### 2. Controlled Simulation

- ✅ **AI-Driven File Sensitivity Analysis** - LightGBM classifier (95% accuracy)- Runs in a **sandboxed environment** to prevent any real-world damage.

- ✅ **Automated Attack Decision Making** - AI determines optimal attack sequence  - Fully configurable to simulate various target scenarios (e.g., Windows 10, Linux).

- ✅ **Enhanced File Enumeration** - Comprehensive filesystem reconnaissance (500+ files)

- ✅ **Pipeline Automation** - Complete workflow from payload → PDF report### 3. Reconnaissance & Intelligence Gathering

- ✅ **Session Tracking** - UUID-based monitoring with real-time status- Scans system for:

- ✅ **Comprehensive Reporting** - Automated PDF/JSON generation  - Open ports

- ✅ **Intelligent Fallbacks** - Works even when AI endpoints offline  - Running processes

  - Sensitive files and directories

---  - Installed software and configurations

- Outputs a detailed report suitable for red team analysis.

## 📊 Quick Overview

### 4. Task Execution (Dummy Operations)

```- Simulates typical malware actions without performing real destructive operations.

┌─────────────────────┐- Actions include:

│   Payload (Agent)   │  Reconnaissance on target system  - File enumeration

│   • System info     │  • Gathers OS, user, privileges  - Process inspection

│   • Port scan       │  • Scans 1-1025 ports    - Network activity simulation

│   • File enum       │  • Enumerates 500+ files

└──────────┬──────────┘### 5. Learning and Adaptation

           │ POST /api/submit_scan/- AI models learn from previous simulations to optimize future behavior.

           ▼- Adaptive prioritization ensures simulated attacks are more efficient over time.

┌─────────────────────┐

│   C2 Server         │  Django backend---

│   • Stores session  │  • Creates UUID session

│   • Triggers AI     │  • Starts pipeline in background## AI Models

└──────────┬──────────┘

           │| Model                   | Purpose                                           | Framework         |

           ▼|-------------------------|--------------------------------------------------|-----------------|

┌─────────────────────┐| Evasion AI              | Detects defensive mechanisms                     | Python / PyTorch |

│  AI Analysis        │  Machine Learning models| Recon Prioritization AI | Scores system findings for attack prioritization| Python / PyTorch |

│  • File sensitivity │  • LightGBM classifier| Attack Decision AI      | Determines next malware action                  | Python / PyTorch |

│  • Attack planning  │  • LightGBM predictor

└──────────┬──────────┘Models are trained on simulated environments for safe evaluation.

           │

           ▼---

┌─────────────────────┐

│  PDF Report         │  Automated documentation## Security Considerations

│  • Risk assessment  │  • Executive summary

│  • Findings         │  • Technical details- **Sandboxed Simulation:** No real damage to system files.

└─────────────────────┘- **No network propagation:** All network activity is simulated.

```- **Logging & Reporting:** Full transparency of actions performed.

- **Strict ethical usage:** For educational and research purposes only.

**Total Time:** ~12-15 seconds from payload execution to PDF report

---

---

## Roadmap

## 🚀 Quick Start

- **Phase 1:** System Reconnaissance (complete)  

### Installation- **Phase 2:** C2 Communication & Task Execution (partial)  

- **Phase 3:** Adaptive AI Learning & Evasion Improvements  

```bash- **Phase 4:** Reporting Enhancements and Visualization  

# Clone repository

git clone <repo-url>---

cd raptor

## License

# Install dependencies  

pip install -r requirements.txtThis project is licensed under the modified MIT License. See the [LICENSE](LICENSE.md) file for details.



# Setup database---

cd src/c2

python manage.py migrate## Disclaimer



# Start C2 serverThis software is intended for **educational and research purposes only**. Unauthorized use on live systems is strictly prohibited. The author is not responsible for any misuse of this software.

python manage.py runserver
```

Server starts at: `http://127.0.0.1:8000`

### Run Enhanced Payload

```bash
cd /path/to/raptor
python3 src/core/payload_v2.py
```

**Output:**
```
🚀 RAPTOR Enhanced Payload v2.0 - Starting Reconnaissance
[1/4] Gathering system information... ✓
[2/4] Scanning network ports... ✓ Found 3 ports
[3/4] Enumerating files... ✓ 500 files found
[4/4] Contacting C2 server... ✓

✅ Reconnaissance complete!
Session ID: 7b70c253-5c4c-4db0-b258-04172370e44d
```

### Check Session Status

```bash
curl http://127.0.0.1:8000/api/session/<session-id>/ | python3 -m json.tool
```

---

## 🧪 Testing

### Run All Tests (33 tests)

```bash
./run_all_tests.sh
```

**Expected:** All 33 tests pass ✅

### Individual Module Tests

```bash
python3 tests/test_models.py         # Module 1: Session tracking
python3 tests/test_orchestrator.py   # Module 2: Pipeline
python3 tests/test_integration.py    # Module 3: API
python3 tests/test_payload.py        # Module 4: Payload (16 tests)
python3 tests/test_e2e_payload.py    # End-to-end workflow
```

---

## 📁 Project Structure

```
raptor/
├── docs/                    # Complete documentation (7 files)
├── src/
│   ├── core/
│   │   ├── payload.py       # Basic payload
│   │   └── payload_v2.py    # ✨ Enhanced with file enumeration
│   └── c2/                  # Django C2 Server
│       ├── scans/           # ✨ Session tracking + orchestrator
│       ├── reconpriority/   # File sensitivity AI
│       ├── attackdecision/  # Attack planning AI
│       └── report/          # PDF generation
├── models/                  # AI model training scripts
├── tests/                   # 33 automated tests
└── run_all_tests.sh        # Test suite runner
```

---

## 🎓 What Makes This Special?

### 1. Complete End-to-End Automation
Unlike typical C2 frameworks, RAPTOR fully automates the workflow:
- Payload executes → Data sent to C2 → AI analyzes → Report generated
- **No manual intervention required**
- Average completion time: 12-15 seconds

### 2. AI-Powered Intelligence  
Two LightGBM models provide intelligent analysis:
- **File Sensitivity Classifier** (95% accuracy, 22 features)
- **Attack Decision Predictor** (10 features, multi-class)

### 3. Intelligent Fallback Mechanisms
If AI endpoints are offline:
- Keyword-based file sensitivity (confidential, password, etc.)
- Risk-based attack planning
- System continues to operate normally

### 4. Production-Ready Architecture
- Session tracking with UUIDs
- Background processing (threading)
- RESTful API design
- Database persistence (SQLite)

### 5. Comprehensive Testing
- 33 automated tests covering all modules
- Unit, integration, and end-to-end tests
- 100% pass rate

---

## 📊 Performance

| Metric | Time |
|--------|------|
| Payload execution (500 files) | ~10 sec |
| Pipeline processing (AI+fallback) | ~2-3 sec |
| **Total (payload → report)** | **~12-15 sec** |

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`architecture.md`](docs/architecture.md) | System architecture |
| [`MODULE_1_COMPLETE.md`](docs/MODULE_1_COMPLETE.md) | Session tracking |
| [`MODULE_2_COMPLETE.md`](docs/MODULE_2_COMPLETE.md) | Pipeline orchestrator |
| [`MODULE_3_COMPLETE.md`](docs/MODULE_3_COMPLETE.md) | API integration |
| [`MODULE_4_COMPLETE.md`](docs/MODULE_4_COMPLETE.md) | Enhanced payload |
| [`PROJECT_SUMMARY.md`](docs/PROJECT_SUMMARY.md) | Complete overview |

---

## 🔒 Security & Ethics

### ⚠️ IMPORTANT DISCLAIMER

This project is **EXCLUSIVELY** for:
- ✅ Educational purposes
- ✅ Authorized penetration testing
- ✅ Security research in controlled environments
- ✅ Personal lab/VM testing

### ❌ NEVER USE FOR:
- Unauthorized access
- Malicious activities
- Privacy violations
- Any illegal purposes

**Use responsibly and only with proper authorization.**

---

## 🛠️ Technology Stack

- **Backend:** Django 5.2.5, Django REST Framework
- **AI/ML:** LightGBM, Scikit-learn
- **Payload:** Python 3.10+, psutil, requests
- **Reporting:** Jinja2, LaTeX
- **Database:** SQLite

---

## 🎯 API Reference

### Submit Scan
```http
POST /api/submit_scan/
Content-Type: application/json

{
  "recon_data": {
    "hostname": "target",
    "files": [...],
    "open_ports": [80, 443]
  }
}
```

### Get Status
```http
GET /api/session/<uuid>/

Response:
{
  "status": "complete",
  "report_path": "generated_reports/report_*.json",
  "summary": {
    "risk_level": "High",
    "findings_count": 5
  }
}
```

---

## 📈 Project Achievements

- ✅ **4 Modules Implemented** - All tested and operational
- ✅ **33 Tests Passing** - Comprehensive coverage
- ✅ **7 Documentation Files** - Complete guides
- ✅ **~2,000 Lines** - New/modified code
- ✅ **12-15 Second** - End-to-end execution

---

## 🤝 Contributing

This is an educational project. Feel free to:
- Report issues
- Suggest enhancements  
- Submit pull requests
- Use for learning

---

## 📄 License

See [LICENSE.md](LICENSE.md) - Educational use only

---

## 🙏 Credits

**Developed For:** College Final Project  
**Purpose:** Educational AI security demonstration  
**Stack:** Django + LightGBM + Python

---

**🎊 RAPTOR v2.0 - Complete AI-Driven Penetration Testing Framework 🎊**

*Built with ❤️ for educational purposes and security research*
