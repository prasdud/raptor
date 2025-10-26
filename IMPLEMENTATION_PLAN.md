# RAPTOR - End-to-End Pipeline Implementation Plan

## Current State Analysis

### ✅ What Works (Tested Individually)
1. **Payload Driver** - Collects recon data and sends to C2
2. **Scans App** - Receives and stores recon data
3. **Recon Priority AI** - Classifies file sensitivity
4. **Attack Decision AI** - Predicts next attack action
5. **Report Generator** - Creates PDF from JSON

### ❌ What's Missing (The Gaps)

1. **Session Management** - No way to track a single pentest session from start to finish
2. **Orchestration Logic** - No controller to coordinate the pipeline
3. **File Enumeration** - Payload doesn't collect actual file lists to send to AI
4. **Bi-directional Communication** - C2 doesn't send attack commands back to payload
5. **Master JSON Builder** - No code to aggregate all data into `sample-payload.json` format
6. **Automatic Report Trigger** - Report generation is manual, not automatic

---

## Proposed Solution: 3 Implementation Approaches

### 🎯 **Approach 1: QUICK & SIMPLE (Recommended for College Project)**
**Timeline**: 1-2 days  
**Complexity**: Low  
**Best for**: Demonstration, presentations, final project defense

#### Changes Required:

1. **Add Session Tracking**
   - Create `Session` model in scans app
   - Track each pentest run with unique ID
   - Store start time, target hostname, status

2. **Enhance Payload Driver**
   - Add file enumeration (list files in common directories)
   - Poll C2 for attack commands
   - Execute dummy attack actions

3. **Create Orchestrator View**
   - New Django view: `orchestrate_pipeline`
   - Triggered when scan data arrives
   - Calls recon AI → attack AI → builds master JSON → generates report
   - Returns report PDF or session ID

4. **Build Master JSON Aggregator**
   - Helper function to combine all data
   - Format: matches `tests/sample-payload.json`
   - Includes recon, AI results, simulated attacks

**Pros**: 
- Fast to implement
- Uses existing code
- Complete demo-able pipeline
- Good for project presentation

**Cons**:
- Semi-automated (some manual steps)
- Not truly "live" C2 interaction
- Simplified attack simulation

---

### 🚀 **Approach 2: SEMI-REALISTIC (Production-Ready)**
**Timeline**: 3-5 days  
**Complexity**: Medium  
**Best for**: Portfolio projects, real red team training

#### Additional Changes:

1. **WebSocket/Long-polling C2**
   - Real-time bidirectional communication
   - Payload receives attack commands instantly
   - Django Channels for WebSocket support

2. **Task Queue System**
   - Celery + Redis for background tasks
   - Async AI inference
   - Report generation as background job

3. **Command Execution Framework**
   - Payload executes received commands
   - Reports results back to C2
   - Implements attack actions: file_enum, process_check, etc.

4. **Dashboard UI**
   - Real-time session monitoring
   - Live attack progress
   - Report download

**Pros**:
- Professional-grade architecture
- Impressive for interviews/portfolio
- Extensible for future features

**Cons**:
- More complex
- Requires additional dependencies
- Longer development time

---

### 🔬 **Approach 3: RESEARCH-GRADE (Advanced)**
**Timeline**: 1-2 weeks  
**Complexity**: High  
**Best for**: Research papers, graduate-level work

#### Advanced Features:

1. **Multi-stage Attack Chains**
   - Attack decision AI loops until complete
   - Adaptive decision based on previous results
   - Learning from successful paths

2. **Evasion AI Integration** (from README)
   - Detect sandbox/VM
   - Adjust payload behavior
   - Third AI model

3. **Adversarial Testing**
   - Test against real AV/EDR (in VM)
   - Measure detection rates
   - Generate ROC curves

---

## 📋 RECOMMENDED: Approach 1 Implementation

Let me provide the **exact code changes** needed:

### Step 1: Add Session Model

**File**: `src/c2/scans/models.py`
```python
from django.db import models
import uuid

class Session(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    target_hostname = models.CharField(max_length=200)
    target_os = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=[
            ('recon', 'Reconnaissance'),
            ('analysis', 'AI Analysis'),
            ('attack', 'Attack Simulation'),
            ('reporting', 'Generating Report'),
            ('complete', 'Complete')
        ],
        default='recon'
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    master_json = models.JSONField(null=True, blank=True)
    report_path = models.CharField(max_length=500, null=True, blank=True)
    
    def __str__(self):
        return f"Session {self.session_id} - {self.target_hostname}"

class ScanResult(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='scans', null=True)
    target = models.CharField(max_length=100)
    os = models.CharField(max_length=200, blank=True, null=True)
    results = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
```

### Step 2: Create Orchestrator

**New File**: `src/c2/scans/orchestrator.py`
```python
import json
import requests
from datetime import datetime
from .models import Session, ScanResult

class PipelineOrchestrator:
    """Orchestrates the complete pentest pipeline"""
    
    def __init__(self, session):
        self.session = session
        self.master_data = {}
    
    def run(self):
        """Execute full pipeline: recon → AI → attacks → report"""
        try:
            # Step 1: Get recon data
            scan_result = self.session.scans.latest('timestamp')
            recon_data = scan_result.results
            
            # Step 2: Enumerate files (simulate or get from recon)
            file_list = self._get_file_enumeration(recon_data)
            
            # Step 3: Run file sensitivity AI
            sensitive_files = self._analyze_file_sensitivity(file_list)
            
            # Step 4: Run attack decision AI
            attack_plan = self._get_attack_decisions(recon_data, sensitive_files)
            
            # Step 5: Build master JSON
            self._build_master_json(recon_data, sensitive_files, attack_plan)
            
            # Step 6: Generate report
            report_path = self._generate_report()
            
            # Step 7: Update session
            self.session.status = 'complete'
            self.session.end_time = datetime.now()
            self.session.report_path = report_path
            self.session.master_json = self.master_data
            self.session.save()
            
            return report_path
            
        except Exception as e:
            self.session.status = 'error'
            self.session.save()
            raise e
    
    def _get_file_enumeration(self, recon_data):
        """Simulate file discovery or extract from recon"""
        # For demo: create sample file list
        # In real scenario: payload would send this
        return [
            {
                "filename": "financial_report_2024.xlsx",
                "extension": ".xlsx",
                "size_kb": 1024,
                "path": "C:/Users/Admin/Documents/Finance/",
                "last_accessed": "2025-10-20"
            },
            {
                "filename": "employee_salaries.csv",
                "extension": ".csv",
                "size_kb": 256,
                "path": "C:/Users/Admin/Documents/HR/",
                "last_accessed": "2025-10-15"
            },
            {
                "filename": "public_notice.pdf",
                "extension": ".pdf",
                "size_kb": 45,
                "path": "C:/Public/",
                "last_accessed": "2025-09-10"
            }
        ]
    
    def _analyze_file_sensitivity(self, file_list):
        """Call recon priority AI"""
        response = requests.post(
            'http://localhost:8000/reconpriority/predict/',
            json=file_list,
            timeout=30
        )
        return response.json()
    
    def _get_attack_decisions(self, recon_data, sensitive_files):
        """Call attack decision AI"""
        summary = sensitive_files.get('summary', {})
        
        attack_input = {
            "count_sensitive_files": summary.get('count_sensitive_files', 0),
            "has_high_sensitivity": summary.get('has_high_sensitivity', 0),
            "max_file_confidence": summary.get('max_file_confidence', 0.0),
            "avg_sensitivity_score": summary.get('avg_sensitivity_score', 0.0),
            "num_open_ports": len(recon_data.get('open_ports', [])),
            "has_web_port": 1 if any(p in [80, 443, 8080] for p in recon_data.get('open_ports', [])) else 0,
            "num_high_ports": len([p for p in recon_data.get('open_ports', []) if p > 1024]),
            "is_admin": 1 if recon_data.get('is_admin') else 0,
            "interesting_env_keys": len([k for k in recon_data.get('env_vars', {}).keys() 
                                         if any(x in k.upper() for x in ['PASSWORD', 'KEY', 'TOKEN', 'SECRET'])]),
            "last_action": "reconnaissance"
        }
        
        response = requests.post(
            'http://localhost:8000/api/attackdecision/',
            json=attack_input,
            timeout=30
        )
        return response.json()
    
    def _build_master_json(self, recon_data, sensitive_files, attack_plan):
        """Build the master JSON for report generation"""
        self.master_data = {
            "target_name": recon_data.get('hostname', 'UNKNOWN'),
            "generated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sim_start": self.session.start_time.strftime('%Y-%m-%d %H:%M'),
            "sim_end": datetime.now().strftime('%Y-%m-%d %H:%M'),
            
            "exec_summary": {
                "purpose": "AI-driven penetration test simulation for security assessment",
                "open_ports_list": [f"{p} - Service detected" for p in recon_data.get('open_ports', [])[:5]],
                "sensitive_data_list": [f"{f['path']}{f['filename']}" for f in sensitive_files.get('files', []) 
                                       if f.get('sensitivity') == 'High'][:5],
                "evasion_success": 85,  # Placeholder
                "av_list": ["Windows Defender (signature-based)"],
                "overall_risk": "Medium",
                "evasion_ai": 85,
                "recon_ai": 92,
                "attack_ai": int(attack_plan.get('confidence', 0.5) * 100)
            },
            
            "scope": {
                "techniques": "Automated reconnaissance, AI-based file sensitivity analysis, intelligent attack planning",
                "phases": [
                    "Phase 1 - System Reconnaissance",
                    "Phase 2 - AI-Powered Threat Analysis",
                    "Phase 3 - Attack Simulation & Reporting"
                ],
                "ai_models": [
                    {
                        "name": "Recon Prioritization AI",
                        "role": "Identifies sensitive files using LightGBM classifier (95% accuracy)"
                    },
                    {
                        "name": "Attack Decision AI",
                        "role": "Predicts optimal attack sequence based on environment state"
                    }
                ]
            },
            
            "recon_data": {
                "os_name": recon_data.get('os_name'),
                "os_version": recon_data.get('os_version'),
                "os_release": recon_data.get('os_release'),
                "architecture": recon_data.get('architecture'),
                "hostname": recon_data.get('hostname'),
                "current_user": recon_data.get('current_user'),
                "machine": recon_data.get('machine'),
                "processor": recon_data.get('processor'),
                "is_admin": recon_data.get('is_admin'),
                "open_ports": [{"number": p, "protocol": "tcp", "service_name": "unknown"} 
                              for p in recon_data.get('open_ports', [])],
                "env_vars_count": len(recon_data.get('env_vars', {}))
            },
            
            "findings": self._generate_findings(recon_data, sensitive_files),
            
            "attacks": [
                {
                    "name": attack_plan.get('predicted_action', 'reconnaissance'),
                    "description": f"AI recommended action based on analysis (confidence: {attack_plan.get('confidence', 0):.2%})",
                    "outcome": "Simulated",
                    "priority": int(attack_plan.get('confidence', 0.5) * 10)
                }
            ],
            
            "mitigations": self._generate_mitigations(recon_data, sensitive_files)
        }
    
    def _generate_findings(self, recon_data, sensitive_files):
        """Generate findings list"""
        findings = []
        
        # Check for sensitive files
        high_sensitive = [f for f in sensitive_files.get('files', []) if f.get('sensitivity') == 'High']
        if high_sensitive:
            findings.append({
                "name": "Sensitive Files Detected",
                "evidence": f"{len(high_sensitive)} high-sensitivity files found",
                "severity": "Critical",
                "impact": "Potential data exposure and exfiltration risk"
            })
        
        # Check for admin access
        if recon_data.get('is_admin'):
            findings.append({
                "name": "Elevated Privileges Detected",
                "evidence": "Payload running with administrator rights",
                "severity": "High",
                "impact": "Full system compromise possible"
            })
        
        # Check for open ports
        if len(recon_data.get('open_ports', [])) > 3:
            findings.append({
                "name": "Multiple Open Ports",
                "evidence": f"{len(recon_data.get('open_ports', []))} ports detected",
                "severity": "Medium",
                "impact": "Increased attack surface"
            })
        
        return findings
    
    def _generate_mitigations(self, recon_data, sensitive_files):
        """Generate mitigation recommendations"""
        mitigations = [
            "Implement principle of least privilege - avoid running applications with admin rights",
            "Encrypt sensitive files and restrict access with proper ACLs",
            "Close unnecessary open ports and services",
            "Deploy endpoint detection and response (EDR) solution",
            "Regular security awareness training for users"
        ]
        return mitigations
    
    def _generate_report(self):
        """Call report generation API"""
        response = requests.post(
            'http://localhost:8000/reports/generate/',
            json=self.master_data,
            timeout=60
        )
        
        # Save PDF
        report_filename = f"RedTeamReport_{self.master_data['target_name']}.pdf"
        report_path = f"generated_reports/{report_filename}"
        
        with open(f"src/c2/{report_path}", 'wb') as f:
            f.write(response.content)
        
        return report_path
```

### Step 3: Update Scan Submission View

**File**: `src/c2/scans/views.py`
```python
import json
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from scans.models import ScanResult, Session
from scans.orchestrator import PipelineOrchestrator

@csrf_exempt
def submit_scan(request):
    """Receives recon data and triggers full pipeline"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            recon_data = data.get("recon_data") or {}
            
            target_ip = recon_data.get("hostname") or "unknown"
            os_name = recon_data.get("os_name") or "unknown"
            
            # Create or get session
            session = Session.objects.create(
                target_hostname=target_ip,
                target_os=os_name,
                status='recon'
            )
            
            # Save scan result
            scan = ScanResult.objects.create(
                session=session,
                target=target_ip,
                os=os_name,
                results=recon_data
            )
            
            # Run orchestrator in background (or immediately for demo)
            orchestrator = PipelineOrchestrator(session)
            try:
                report_path = orchestrator.run()
                
                return JsonResponse({
                    "status": "success",
                    "session_id": str(session.session_id),
                    "report_path": report_path,
                    "message": "Pipeline completed successfully"
                })
            except Exception as e:
                return JsonResponse({
                    "status": "partial_success",
                    "session_id": str(session.session_id),
                    "message": f"Scan saved but pipeline failed: {str(e)}"
                }, status=500)
                
        except Exception as e:
            print("Error saving scan result:", e)
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    else:
        return JsonResponse({
            "status": "error",
            "message": "POST request required"
        }, status=400)
```

### Step 4: Enhanced Payload with File Enumeration

**File**: `src/core/payload_v2.py` (new version)
```python
import platform
import os
import getpass
import socket
import psutil
import ctypes
import json
import requests
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def enumerate_files():
    """Enumerate files in common directories"""
    files_found = []
    
    # Common directories to scan (Windows)
    if platform.system() == "Windows":
        scan_paths = [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Desktop"),
            "C:/Users/Public"
        ]
    else:
        scan_paths = [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Desktop"),
            "/tmp"
        ]
    
    for base_path in scan_paths:
        if not os.path.exists(base_path):
            continue
            
        try:
            for root, dirs, files in os.walk(base_path):
                # Limit depth
                if root.count(os.sep) - base_path.count(os.sep) > 2:
                    continue
                
                for filename in files[:50]:  # Limit files per directory
                    try:
                        file_path = os.path.join(root, filename)
                        stat_info = os.stat(file_path)
                        
                        files_found.append({
                            "filename": filename,
                            "extension": Path(filename).suffix or "none",
                            "size_kb": round(stat_info.st_size / 1024, 2),
                            "path": root + "/",
                            "last_accessed": str(datetime.fromtimestamp(stat_info.st_atime).date())
                        })
                    except Exception as e:
                        logging.debug(f"Error accessing file {filename}: {e}")
                        continue
                        
        except Exception as e:
            logging.warning(f"Error scanning {base_path}: {e}")
            continue
    
    logging.info(f"Enumerated {len(files_found)} files")
    return files_found

# ... (keep existing recon code) ...

# Add file enumeration
logging.info("Starting file enumeration...")
file_list = enumerate_files()

# Update payload to include files
payload = {
    "recon_data": {
        # ... existing recon data ...
        "files": file_list  # ADD THIS
    }
}

# Send to C2
c2_url = "http://localhost:8000/api/submit_scan/"  # Update to localhost for testing
# ... rest of sending code ...
```

### Step 5: Add Session Status Endpoint

**New endpoint**: `src/c2/scans/urls.py`
```python
from django.urls import path
from .views import submit_scan, get_session_status

urlpatterns = [
    path('submit_scan/', submit_scan),
    path('session/<uuid:session_id>/', get_session_status),
]
```

**New view**: `src/c2/scans/views.py`
```python
def get_session_status(request, session_id):
    """Get status of a pentest session"""
    try:
        session = Session.objects.get(session_id=session_id)
        return JsonResponse({
            "session_id": str(session.session_id),
            "target": session.target_hostname,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "report_path": session.report_path
        })
    except Session.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)
```

---

## Testing the Complete Pipeline

### Quick Test Script

**File**: `tests/test_pipeline.py`
```python
import requests
import json
import time

# 1. Load sample recon data
with open('tests/sample_recon.json') as f:
    recon_data = json.load(f)

# 2. Submit to C2
print("🚀 Submitting recon data...")
response = requests.post(
    'http://localhost:8000/api/submit_scan/',
    json={"recon_data": recon_data}
)

result = response.json()
print(f"✅ Response: {result}")

if result['status'] == 'success':
    session_id = result['session_id']
    report_path = result['report_path']
    
    print(f"📊 Session ID: {session_id}")
    print(f"📄 Report: {report_path}")
    print("\n✅ PIPELINE COMPLETE!")
else:
    print("❌ Pipeline failed")
```

---

## Implementation Timeline

### Day 1: Core Pipeline
- [ ] Create Session model & migrate database
- [ ] Implement orchestrator.py
- [ ] Update submit_scan view
- [ ] Test with existing data

### Day 2: Integration
- [ ] Add file enumeration to payload
- [ ] Test end-to-end flow
- [ ] Fix bugs and edge cases
- [ ] Generate sample reports

### Day 3: Polish
- [ ] Add error handling
- [ ] Improve logging
- [ ] Create demo script
- [ ] Update documentation

---

## Next Steps

Would you like me to:
1. **Implement Approach 1** (create all the files above)
2. **Just create the orchestrator** (minimum viable pipeline)
3. **Show a different approach** (WebSocket-based, etc.)

For your college project, I recommend **Option 1** - it gives you a complete, demo-able system that shows the full AI pipeline in action!
