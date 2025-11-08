# RAPTOR - Red Team AI Malware Simulator
## Complete System Architecture

> **Educational Purpose Notice**: This project is designed for cybersecurity education and controlled red team operations only. It simulates malware behavior in isolated lab environments to help security professionals understand advanced attack patterns.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [AI Models](#ai-models)
6. [API Endpoints](#api-endpoints)
7. [Technology Stack](#technology-stack)
8. [Deployment Architecture](#deployment-architecture)

---

## System Overview

RAPTOR is a sophisticated red team simulation platform that combines AI-driven decision-making with traditional malware emulation techniques. The system consists of:

- **Payload Driver**: Windows-based reconnaissance agent deployed on target VM
- **C2 Server**: Django-based command & control server with AI decision engines
- **AI Models**: Machine learning models for recon prioritization and attack planning
- **Report Generator**: Automated PDF report generation with LaTeX

### Key Capabilities
✅ System reconnaissance and fingerprinting  
✅ AI-powered file sensitivity classification  
✅ Intelligent attack decision-making  
✅ Comprehensive PDF report generation  
✅ Safe simulation with dummy operations  

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TARGET ENVIRONMENT                          │
│                    (Windows 10 VM - Isolated)                       │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │                    PAYLOAD DRIVER                          │    │
│  │                  (src/core/payload.py)                     │    │
│  │                                                            │    │
│  │  • System Fingerprinting                                   │    │
│  │  • Port Scanning (1-101)                                   │    │
│  │  • Process Enumeration                                     │    │
│  │  • Environment Variable Collection                         │    │
│  │  • Admin Rights Detection                                  │    │
│  │                                                            │    │
│  └─────────────────────────┬──────────────────────────────────┘    │
│                            │                                        │
│                            │ HTTP POST                              │
│                            │ /api/submit_scan/                      │
└────────────────────────────┼────────────────────────────────────────┘
                             │
                             │ JSON Payload (Recon Data)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          C2 SERVER                                  │
│                    (Django Application)                             │
│                      Port: 8000                                     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      DJANGO APPS                              │  │
│  │                                                               │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐       │  │
│  │  │   scans/    │  │reconpriority/│  │attackdecision/│       │  │
│  │  │             │  │              │  │               │       │  │
│  │  │ • Store     │  │ • File       │  │ • Attack      │       │  │
│  │  │   recon     │  │   sensitivity│  │   planning    │       │  │
│  │  │   data      │  │   AI         │  │ • Next action │       │  │
│  │  │ • SQLite DB │  │ • LightGBM   │  │   selection   │       │  │
│  │  │             │  │   classifier │  │ • LightGBM    │       │  │
│  │  └─────────────┘  └──────────────┘  └───────────────┘       │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────┐         │  │
│  │  │              report/                             │         │  │
│  │  │                                                  │         │  │
│  │  │  • LaTeX/Jinja2 Template Rendering              │         │  │
│  │  │  • PDF Generation (pdflatex)                    │         │  │
│  │  │  • Chart Generation (matplotlib)                │         │  │
│  │  │  • Comprehensive Security Reports               │         │  │
│  │  └─────────────────────────────────────────────────┘         │  │
│  │                                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Database: SQLite (db.sqlite3)                                     │
│  Storage: generated_reports/, media/reports/                       │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             │
                             ▼
                    ┌─────────────────┐
                    │  PDF REPORT     │
                    │  DELIVERY       │
                    └─────────────────┘
```

---

## Component Details

### 1. Payload Driver (`src/core/payload.py`)

**Purpose**: Lightweight reconnaissance agent deployed on target Windows 10 VM

**Capabilities**:
- **System Fingerprinting**
  - OS name, version, release, architecture
  - Hostname, current user, admin privileges
  - Machine type, processor info
  - Python environment details
  
- **Network Reconnaissance**
  - Port scanning (ports 1-101)
  - Socket connection testing
  - Active listening ports via `psutil`
  - Network interface enumeration
  
- **Environment Collection**
  - All environment variables
  - Active processes and PIDs
  - User account information
  
- **C2 Communication**
  - HTTP POST to `http://85.215.240.40:8000/api/submit_scan/`
  - JSON payload transmission
  - Local logging to `logs.json`

**Security Considerations**:
- ✅ Runs in controlled VM environment
- ✅ Limited port scanning range (1-101)
- ✅ No destructive operations
- ✅ Full activity logging

**Compiled Version**: 
- Built with PyInstaller (spec file: `payload.spec`)
- Standalone executable for deployment

---

### 2. C2 Server (`src/c2/`)

**Architecture**: Django 5.2.5 monolithic application with modular apps

**Core Configuration** (`c2/settings.py`):
- Django REST Framework enabled
- SQLite database
- Jinja2 template engine for LaTeX
- Django templates for HTML
- CSRF exempt endpoints for API
- DEBUG mode (development)

**URL Routing** (`c2/urls.py`):
```
/admin/                          → Django Admin
/api/submit_scan/                → Scan ingestion endpoint
/reconpriority/predict/          → File sensitivity prediction
/api/attackdecision/             → Attack planning endpoint
/reports/generate/               → PDF report generation
```

---

### 3. Django Apps

#### 3.1 **scans/** - Reconnaissance Data Storage

**Purpose**: Ingest and store reconnaissance data from payload

**Models** (`models.py`):
```python
class ScanResult:
    - target: CharField (hostname/IP)
    - os: CharField (OS name)
    - results: JSONField (complete recon data)
    - timestamp: DateTimeField (auto-generated)
```

**Views** (`views.py`):
- `submit_scan()`: POST endpoint for payload data
  - Accepts JSON payload with `recon_data` key
  - Extracts hostname, OS, full recon results
  - Stores in SQLite database
  - Returns success/error JSON response

**Endpoint**: `POST /api/submit_scan/`

**Sample Request**:
```json
{
  "recon_data": {
    "hostname": "WIN10-VM",
    "os_name": "Windows",
    "os_version": "10.0.19044",
    "architecture": "64bit",
    "current_user": "admin",
    "is_admin": true,
    "open_ports": [80, 443, 3389],
    "env_vars": {...}
  }
}
```

---

#### 3.2 **reconpriority/** - File Sensitivity AI

**Purpose**: AI-powered classification of file sensitivity using trained ML model

**Model Architecture**:
- **Algorithm**: LightGBM Classifier
- **Model File**: `file_sensitivity_model.pkl` (joblib serialized)
- **Training**: `src/models/recon-priority/main/trainer.py`

**Features** (22 total):
1. **File Metadata**:
   - `filesize_kb`: File size in KB
   - `extension`: File type (.pdf, .xlsx, .csv, etc.)
   
2. **Path Analysis**:
   - `department`: Extracted from path (Finance, HR, etc.)
   - `subdirectory`: Second-level directory
   - `path_depth`: Directory nesting level
   - `in_sensitive_folder`: Boolean for sensitive paths
   
3. **Filename Pattern Matching**:
   - `has_confidential`: Matches "confidential|private|secret|internal"
   - `has_financial`: Matches "ledger|account|payment|invoice|salary"
   - `has_medical`: Matches "patient|medical|health|lab|diagnosis"
   - `has_legal`: Matches "agreement|contract|legal|nda"
   - `has_personal`: Matches "personal|ssn|dob|employee"
   - `doc_type`: Report, ledger, agreement, policy, etc.
   - `has_numbers`: Contains numeric IDs
   
4. **Temporal Features**:
   - `year`, `month`, `day_of_week`: From last accessed date
   - `is_recent`: Modified after 2024-01-01
   
5. **Size Categories**:
   - `size_category`: small (<50KB), medium (<200KB), large (<1MB), very_large

**Training Details**:
- **Dataset**: `improved_dataset.csv` (synthetic finance/healthcare data)
- **Algorithm**: LightGBM with 500 estimators
- **Hyperparameters**:
  - Learning rate: 0.03
  - Max depth: 8
  - Num leaves: 50
  - Class weight: balanced
  - Scale pos weight: 1.8 (for sensitivity class)
- **Performance**: ~95%+ accuracy (from training metrics)

**Endpoint**: `POST /reconpriority/predict/`

**Sample Request**:
```json
[
  {
    "filename": "confidential_report.pdf",
    "extension": ".pdf",
    "size_kb": 2048,
    "path": "C:/Finance/Accounts/",
    "last_accessed": "2025-08-14"
  }
]
```

**Sample Response**:
```json
{
  "files": [
    {
      "filename": "confidential_report.pdf",
      "sensitivity": "High",
      "sensitivity_binary": 1,
      "path": "C:/Finance/Accounts/",
      "confidence": 0.95
    }
  ],
  "summary": {
    "count_sensitive_files": 1,
    "has_high_sensitivity": 1,
    "max_file_confidence": 0.95,
    "avg_sensitivity_score": 0.95
  }
}
```

---

#### 3.3 **attackdecision/** - Attack Planning AI

**Purpose**: Predict next simulated attack action based on environment state

**Model Architecture**:
- **Algorithm**: LightGBM Multi-class Classifier
- **Model Files**:
  - `attack_decision_lgbm_model.pkl`: Trained model
  - `action_label_encoder.pkl`: Action label encoder
  - `last_action_encoder.pkl`: Previous action encoder
- **Training**: `src/models/attack-decision/main/trainer.py`

**Input Features** (10 total):
1. `count_sensitive_files`: Number of sensitive files detected
2. `has_high_sensitivity`: Boolean for high-confidence sensitive files
3. `max_file_confidence`: Highest sensitivity score
4. `avg_sensitivity_score`: Average sensitivity across files
5. `num_open_ports`: Total open ports found
6. `has_web_port`: Boolean for ports 80/443/8080
7. `num_high_ports`: Ports above 1024
8. `is_admin`: Boolean for admin privileges
9. `interesting_env_keys`: Count of sensitive environment variables
10. `last_action_encoded`: Previously executed action (encoded)

**Output Actions** (Sample):
- `file_enumeration`: List files in sensitive directories
- `process_inspection`: Examine running processes
- `network_scan`: Deeper port/service scanning
- `privilege_escalation`: Attempt to gain higher privileges
- `credential_harvesting`: Look for stored credentials
- `lateral_movement`: Attempt to move to other systems
- `data_exfiltration`: Simulate data theft
- `persistence`: Install simulated backdoor

**Training Details**:
- **Dataset**: `attack_decision_dataset_windows.csv` (synthetic attack scenarios)
- **Algorithm**: LightGBM GBDT
- **Hyperparameters**:
  - Objective: multiclass
  - Learning rate: 0.1
  - Num leaves: 31
  - Max depth: 6
  - Boosting rounds: 200 (with early stopping)

**Endpoint**: `POST /api/attackdecision/`

**Sample Request**:
```json
{
  "count_sensitive_files": 5,
  "has_high_sensitivity": 1,
  "max_file_confidence": 0.92,
  "avg_sensitivity_score": 0.78,
  "num_open_ports": 3,
  "has_web_port": 1,
  "num_high_ports": 2,
  "is_admin": 1,
  "interesting_env_keys": 4,
  "last_action": "reconnaissance"
}
```

**Sample Response**:
```json
{
  "predicted_action": "data_exfiltration",
  "confidence": 0.87
}
```

---

#### 3.4 **report/** - PDF Report Generation

**Purpose**: Generate comprehensive security assessment reports in PDF format

**Technology Stack**:
- **Template Engine**: Jinja2 (for LaTeX)
- **PDF Compiler**: pdflatex (LaTeX to PDF)
- **Charts**: matplotlib (PNG charts embedded in PDF)
- **Template**: `templates/report/report_template.tex`

**Report Sections**:
1. **Executive Summary**
   - Simulation purpose
   - Open ports discovered
   - Sensitive files identified
   - Evasion success rate
   - AV/EDR detected
   - Overall risk assessment
   
2. **Scope & Methodology**
   - Testing techniques
   - Simulation phases
   - AI models used (Evasion, Recon Priority, Attack Decision)
   
3. **Reconnaissance Data**
   - OS information
   - Architecture & patches
   - Installed software
   - User accounts
   - Network configuration
   - Open ports with vulnerabilities
   - Active processes
   - Connected devices
   - Misconfigurations
   
4. **Findings**
   - Severity-ranked vulnerabilities
   - Evidence for each finding
   - Impact assessment
   
5. **Evasion Analysis**
   - Detection mechanisms encountered
   - AV/EDR systems
   - VM/Sandbox detection
   - Success rates per defense
   - Actions skipped due to detection risk
   
6. **Simulated Attacks**
   - Attack name and description
   - Outcome (success/failed/skipped)
   - Priority ranking
   
7. **Recommendations**
   - Actionable mitigation steps
   - Security hardening guidance
   
8. **Raw Data**
   - Complete JSON dump of all collected data

**Endpoint**: `POST /reports/generate/`

**Sample Request**: See `tests/sample-payload.json` for complete example

**Output**:
- PDF file: `RedTeamReport_{hostname}.pdf`
- Saved to: `src/c2/generated_reports/`
- Charts: `evasion_chart.png`, etc.

**Chart Generation**:
```python
# Pie chart for evasion success rates
generate_chart(
    data_list=[90, 78, 82, 75],
    labels=['AV', 'Process Detection', 'Network IDS', 'File Monitoring'],
    out_path='evasion_chart.png',
    chart_type='pie'
)
```

---

## Data Flow

### Complete Attack Simulation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PHASE 1: RECON                             │
└─────────────────────────────────────────────────────────────────────┘
  
  1. Payload driver executes on target VM
     ↓
  2. Collects system fingerprint (OS, user, processes, ports, env vars)
     ↓
  3. HTTP POST → C2 Server (/api/submit_scan/)
     ↓
  4. Stored in ScanResult model (SQLite)

┌─────────────────────────────────────────────────────────────────────┐
│                   PHASE 2: AI ANALYSIS                              │
└─────────────────────────────────────────────────────────────────────┘

  5. File list extracted from recon data
     ↓
  6. POST → /reconpriority/predict/
     ↓
  7. LightGBM classifier predicts sensitivity (High/Low + confidence)
     ↓
  8. Response contains:
     - Per-file sensitivity scores
     - Summary statistics (count_sensitive_files, max_confidence, etc.)
     ↓
  9. Combine with recon data (ports, admin status, env vars)
     ↓
  10. POST → /api/attackdecision/
     ↓
  11. LightGBM classifier predicts next attack action
     ↓
  12. Response: { "predicted_action": "...", "confidence": 0.XX }

┌─────────────────────────────────────────────────────────────────────┐
│                  PHASE 3: REPORTING                                 │
└─────────────────────────────────────────────────────────────────────┘

  13. Aggregate all data:
      - Original recon data
      - File sensitivity results
      - Attack decisions
      - Simulated attack outcomes
     ↓
  14. POST → /reports/generate/
     ↓
  15. Jinja2 renders LaTeX template
     ↓
  16. pdflatex compiles → PDF
     ↓
  17. PDF returned via HTTP response
     ↓
  18. Red team professional reviews report
```

---

## AI Models

### Model 1: Recon Prioritization (File Sensitivity Classifier)

**Location**: `src/models/recon-priority/`

**Training Pipeline** (`main/trainer.py`):

```python
class FileSensitivityClassifier:
    - extract_features(): 22 engineered features
    - preprocess_features(): LabelEncoder for categoricals
    - train(): LightGBM training with cross-validation
    - save_model(): Pickle model + encoders
    - predict(): Inference on new files
```

**Dataset Generation**:
- `finance-data-generation.py`: Synthetic finance file metadata
- `healthcare-data-generation.py`: Synthetic healthcare file metadata
- `master-data-generator.py`: Combined dataset creator
- **Output**: `master-finance-data-binary.csv`, `master-health-data-binary.csv`

**Data Cleaning** (`data-cleaner.py`):
- Removes duplicates
- Balances classes
- Feature validation
- **Output**: `improved_dataset.csv`

**Model Performance** (from training):
- Accuracy: ~95%
- ROC-AUC: ~0.96
- Strong recall for sensitive files
- Top features: `has_financial`, `has_confidential`, `department`, `extension`

---

### Model 2: Attack Decision (Action Predictor)

**Location**: `src/models/attack-decision/`

**Training Pipeline** (`main/trainer.py`):

```python
# Feature engineering
- Encode last_action with LabelEncoder
- 10 numerical/categorical features

# LightGBM multi-class training
lgb.train(
    params={'objective': 'multiclass', 'num_class': N_actions},
    num_round=200,
    early_stopping_rounds=20
)

# Outputs
- attack_decision_lgbm_model.pkl
- action_label_encoder.pkl
- last_action_encoder.pkl
- confusion_matrix.png
- feature_importance.png
```

**Dataset** (`attack_decision_dataset_windows.csv`):
- Synthetic attack scenarios for Windows environments
- Features: sensitivity metrics, network state, privilege level, previous action
- Labels: Next recommended attack action

**Key Features by Importance**:
1. `count_sensitive_files`: Strong indicator for exfiltration
2. `is_admin`: Enables privilege-dependent actions
3. `has_high_sensitivity`: Triggers high-value target actions
4. `num_open_ports`: Network-based attack opportunities
5. `last_action_encoded`: Sequential decision context

---

## API Endpoints

### 1. Scan Submission
```
POST /api/submit_scan/
Content-Type: application/json

Request:
{
  "recon_data": {
    "hostname": "string",
    "os_name": "string",
    "os_version": "string",
    "architecture": "string",
    "current_user": "string",
    "is_admin": boolean,
    "open_ports": [int],
    "env_vars": {}
  }
}

Response:
{
  "status": "success" | "error",
  "message": "string" (if error)
}
```

---

### 2. File Sensitivity Prediction
```
POST /reconpriority/predict/
Content-Type: application/json

Request:
[
  {
    "filename": "string",
    "extension": "string",
    "size_kb": number,
    "path": "string",
    "last_accessed": "YYYY-MM-DD"
  }
]

Response:
{
  "files": [
    {
      "filename": "string",
      "sensitivity": "High" | "Low",
      "sensitivity_binary": 1 | 0,
      "path": "string",
      "confidence": number
    }
  ],
  "summary": {
    "count_sensitive_files": number,
    "has_high_sensitivity": 0 | 1,
    "max_file_confidence": number,
    "avg_sensitivity_score": number
  }
}
```

---

### 3. Attack Decision
```
POST /api/attackdecision/
Content-Type: application/json

Request:
{
  "count_sensitive_files": number,
  "has_high_sensitivity": 0 | 1,
  "max_file_confidence": number,
  "avg_sensitivity_score": number,
  "num_open_ports": number,
  "has_web_port": 0 | 1,
  "num_high_ports": number,
  "is_admin": 0 | 1,
  "interesting_env_keys": number,
  "last_action": "string"
}

Response:
{
  "predicted_action": "string",
  "confidence": number
}
```

---

### 4. Report Generation
```
POST /reports/generate/
Content-Type: application/json

Request: See tests/sample-payload.json

Response:
Content-Type: application/pdf
Content-Disposition: attachment; filename="RedTeamReport_{target}.pdf"

[Binary PDF data]
```

---

## Technology Stack

### Backend
- **Framework**: Django 5.2.5
- **API**: Django REST Framework
- **Database**: SQLite (db.sqlite3)
- **Template Engines**: Django templates, Jinja2

### AI/ML
- **Library**: LightGBM (gradient boosting)
- **Data Processing**: pandas, numpy
- **Model Serialization**: joblib
- **Metrics**: scikit-learn

### Payload
- **Language**: Python 3.x
- **System Info**: platform, psutil, socket, ctypes
- **Networking**: requests
- **Packaging**: PyInstaller

### Reporting
- **PDF Generation**: pdflatex (LaTeX)
- **Charts**: matplotlib, seaborn
- **Templates**: Jinja2 for LaTeX

### Development Tools
- **Version Control**: Git (GitHub: prasdud/raptor)
- **Branch**: dev
- **Package Management**: pip (requirements.txt)

---

## Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────────────────────────┐
│                     Development Machine                     │
│                                                             │
│  /home/prasdud/playground/raptor/                          │
│  ├── src/c2/                  (Django C2 Server)           │
│  ├── src/core/                (Payload Builder)            │
│  ├── src/models/              (AI Training Scripts)        │
│  └── tests/                   (Sample Data)                │
│                                                             │
│  Run: python manage.py runserver 0.0.0.0:8000             │
└─────────────────────────────────────────────────────────────┘
```

### Lab Environment (Recommended)

```
┌──────────────────────────────────────────────────────────────────┐
│                      ISOLATED VIRTUAL NETWORK                    │
│                        (No Internet Access)                      │
│                                                                  │
│  ┌─────────────────────────┐      ┌──────────────────────────┐  │
│  │   C2 Server             │      │   Target VM              │  │
│  │   (Ubuntu/Debian)       │      │   (Windows 10)           │  │
│  │                         │      │                          │  │
│  │  • Django on 8000       │◄─────┤  • Payload driver        │  │
│  │  • SQLite database      │      │  • Recon agent           │  │
│  │  • LaTeX installed      │      │  • Isolated from         │  │
│  │  • Python 3.10+         │      │    production networks   │  │
│  └─────────────────────────┘      └──────────────────────────┘  │
│           ▲                                                      │
│           │                                                      │
│  ┌────────┴──────────────────┐                                  │
│  │  Red Team Workstation     │                                  │
│  │  • Access C2 web UI       │                                  │
│  │  • Download reports       │                                  │
│  │  • Monitor simulations    │                                  │
│  └───────────────────────────┘                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Security Considerations

⚠️ **Critical Safety Measures**:

1. **Network Isolation**
   - C2 and target VMs must be on isolated virtual network
   - No internet connectivity during active simulations
   - Firewall rules preventing external communication
   
2. **VM Snapshots**
   - Take clean snapshots before each simulation
   - Restore to clean state after testing
   - Never run on production systems
   
3. **Access Control**
   - C2 server requires authentication (add in production)
   - Limit physical access to lab environment
   - Audit all activities
   
4. **Data Sanitization**
   - Use synthetic data for training
   - No real credentials or PII in test files
   - Secure disposal of simulation artifacts
   
5. **Legal Compliance**
   - Obtain written authorization for all testing
   - Document scope and limitations
   - Maintain chain of custody for reports

---

## File Structure Reference

```
raptor/
├── LICENSE.md                      # Modified MIT license
├── README.md                       # Project overview
├── ARCHITECTURE.md                 # This document
├── requirements.txt                # Python dependencies
├── logs.json                       # Payload execution logs
│
├── docs/
│   └── architecture.md             # Original architecture notes
│
├── src/
│   ├── core/                       # Payload driver
│   │   ├── payload.py              # Main reconnaissance script
│   │   ├── payload.spec            # PyInstaller spec
│   │   └── build/                  # Compiled payloads
│   │
│   ├── c2/                         # Django C2 server
│   │   ├── manage.py               # Django management
│   │   ├── db.sqlite3              # Database
│   │   │
│   │   ├── c2/                     # Main Django project
│   │   │   ├── settings.py         # Configuration
│   │   │   ├── urls.py             # URL routing
│   │   │   ├── wsgi.py             # WSGI application
│   │   │   └── jinja2_env.py       # Jinja2 config
│   │   │
│   │   ├── scans/                  # Recon data ingestion app
│   │   │   ├── models.py           # ScanResult model
│   │   │   ├── views.py            # submit_scan endpoint
│   │   │   └── urls.py             # /api/submit_scan/
│   │   │
│   │   ├── reconpriority/          # File sensitivity AI app
│   │   │   ├── views.py            # Prediction endpoint
│   │   │   ├── urls.py             # /reconpriority/predict/
│   │   │   └── file_sensitivity_model.pkl  # Trained model
│   │   │
│   │   ├── attackdecision/         # Attack planning AI app
│   │   │   ├── views.py            # Decision endpoint
│   │   │   ├── urls.py             # /api/attackdecision/
│   │   │   ├── attack_decision_lgbm_model.pkl
│   │   │   ├── action_label_encoder.pkl
│   │   │   └── last_action_encoder.pkl
│   │   │
│   │   ├── report/                 # PDF generation app
│   │   │   ├── views.py            # generate_report endpoint
│   │   │   ├── urls.py             # /reports/generate/
│   │   │   └── templates/
│   │   │       └── report/
│   │   │           └── report_template.tex
│   │   │
│   │   ├── jinja_templates/        # LaTeX templates
│   │   │   └── report_template.tex
│   │   │
│   │   └── generated_reports/      # Output PDFs
│   │       ├── RedTeamReport_*.pdf
│   │       └── evasion_chart.png
│   │
│   └── models/                     # AI training code
│       ├── recon-priority/
│       │   ├── main/
│       │   │   ├── trainer.py      # LightGBM training script
│       │   │   └── improved_dataset.csv
│       │   ├── finance-data-generation.py
│       │   ├── healthcare-data-generation.py
│       │   └── master-data-generator.py
│       │
│       └── attack-decision/
│           ├── main/
│           │   └── trainer.py      # Attack decision training
│           └── attack_decision_dataset_windows.csv
│
└── tests/
    └── sample-payload.json         # Example report request
```

---

## Dependencies

```
# Core Framework
Django==5.2.5
djangorestframework (via settings)
asgiref==3.9.1
sqlparse==0.5.3
typing_extensions==4.15.0

# System Monitoring (Payload)
psutil==7.0.0

# AI/ML (Training - not in requirements.txt)
lightgbm
pandas
numpy
scikit-learn
joblib
matplotlib
seaborn

# Report Generation (System-level)
pdflatex (TeX Live or MiKTeX)
```

---

## Future Enhancements (Not Currently Implemented)

From README.md roadmap:

- **Evasion AI**: Sandbox/VM detection (referenced but not implemented)
- **Adaptive Learning**: AI models learning from simulations
- **Network Propagation**: Currently all network activity is simulated
- **Advanced Evasion**: Dynamic payload obfuscation
- **Real-time C2**: Bi-directional command execution
- **Visualization Dashboard**: Web UI for monitoring

---

## Educational Use Cases

This platform is designed for:

1. **Red Team Training**
   - Learn attack patterns and decision flows
   - Practice report writing
   - Understand AI-driven malware behavior
   
2. **Blue Team Defense**
   - Test detection capabilities
   - Validate security controls
   - Improve incident response
   
3. **Security Research**
   - Study ML-based attack decision-making
   - Analyze reconnaissance techniques
   - Benchmark evasion strategies
   
4. **Academic Projects**
   - Final year college projects (like this one!)
   - Cybersecurity coursework
   - ML in security applications

---

## Conclusion

RAPTOR demonstrates the intersection of AI and cybersecurity, providing a safe platform to study advanced malware behavior. The modular architecture allows easy extension and customization for various educational scenarios.

**Key Achievements**:
✅ Full-stack Django C2 server  
✅ AI-powered file sensitivity detection (95% accuracy)  
✅ Intelligent attack planning with LightGBM  
✅ Professional PDF report generation  
✅ Safe, controlled simulation environment  

**Remember**: This is an educational tool. Always obtain proper authorization and use in isolated environments only.

---

*Architecture Document Version 1.0*  
*Last Updated: October 26, 2025*  
*Project: RAPTOR - Red Team AI Malware Simulator*  
*Author: prasdud*  
*Branch: dev*
