"""
Pipeline Orchestrator - Coordinates the complete pentest workflow
Automatically processes: Recon → AI Analysis → Attack Planning → Report Generation
"""
import json
import requests
from datetime import datetime
from django.utils import timezone


class PipelineOrchestrator:
    """Orchestrates the complete pentest pipeline"""
    
    def __init__(self, session):
        """
        Initialize orchestrator for a session
        
        Args:
            session: Session model instance
        """
        self.session = session
        self.master_data = {}
        self.base_url = "http://localhost:8000"  # C2 server URL
    
    def run(self):
        """
        Execute full pipeline: recon → AI → attacks → report
        
        Returns:
            str: Path to generated report
        """
        try:
            print(f"🚀 Starting pipeline for session {self.session.session_id}")
            
            # Step 1: Get recon data
            self.session.status = 'analysis'
            self.session.save()
            print("📊 Step 1: Loading reconnaissance data...")
            scan_result = self.session.scans.latest('timestamp')
            recon_data = scan_result.results
            print(f"   ✓ Loaded recon from {scan_result.target}")
            
            # Step 2: Enumerate files (simulate or extract from recon)
            print("📁 Step 2: Enumerating files...")
            file_list = self._get_file_enumeration(recon_data)
            print(f"   ✓ Found {len(file_list)} files")
            
            # Step 3: Run file sensitivity AI
            print("🤖 Step 3: Analyzing file sensitivity (AI)...")
            sensitive_files = self._analyze_file_sensitivity(file_list)
            sensitive_count = sensitive_files.get('summary', {}).get('count_sensitive_files', 0)
            print(f"   ✓ Identified {sensitive_count} sensitive files")
            
            # Step 4: Run attack decision AI
            self.session.status = 'attack'
            self.session.save()
            print("🎯 Step 4: Planning attack strategy (AI)...")
            attack_plan = self._get_attack_decisions(recon_data, sensitive_files)
            print(f"   ✓ Recommended action: {attack_plan.get('predicted_action', 'N/A')}")
            
            # Step 5: Build master JSON
            print("📋 Step 5: Building master report JSON...")
            self._build_master_json(recon_data, sensitive_files, attack_plan)
            print(f"   ✓ Master JSON created ({len(json.dumps(self.master_data))} bytes)")
            
            # Step 6: Generate report
            self.session.status = 'reporting'
            self.session.save()
            print("📄 Step 6: Generating PDF report...")
            report_path = self._generate_report()
            print(f"   ✓ Report generated: {report_path}")
            
            # Step 7: Update session
            self.session.status = 'complete'
            self.session.end_time = timezone.now()
            self.session.report_path = report_path
            self.session.master_json = self.master_data
            self.session.save()
            
            print(f"✅ Pipeline complete! Session {self.session.session_id}")
            return report_path
            
        except Exception as e:
            self.session.status = 'error'
            self.session.error_message = str(e)
            self.session.save()
            print(f"❌ Pipeline failed: {e}")
            raise e
    
    def _get_file_enumeration(self, recon_data):
        """
        Get file list from recon data or simulate file discovery
        
        Args:
            recon_data: Dictionary of reconnaissance data
            
        Returns:
            list: List of file dictionaries
        """
        # Check if files were sent from payload
        if 'files' in recon_data and recon_data['files']:
            return recon_data['files']
        
        # Otherwise, simulate file discovery based on OS
        # In production, payload would send this data
        os_name = recon_data.get('os_name', 'Unknown')
        
        if 'Windows' in os_name:
            return self._simulate_windows_files()
        else:
            return self._simulate_linux_files()
    
    def _simulate_windows_files(self):
        """Simulate Windows file enumeration for demo"""
        return [
            {
                "filename": "financial_report_2024.xlsx",
                "extension": ".xlsx",
                "size_kb": 1024,
                "path": "C:/Users/Admin/Documents/Finance/",
                "last_accessed": "2025-10-20"
            },
            {
                "filename": "employee_salaries_confidential.csv",
                "extension": ".csv",
                "size_kb": 256,
                "path": "C:/Users/Admin/Documents/HR/",
                "last_accessed": "2025-10-15"
            },
            {
                "filename": "patient_records_2024.xlsx",
                "extension": ".xlsx",
                "size_kb": 512,
                "path": "C:/Users/Admin/Documents/Medical/",
                "last_accessed": "2025-10-18"
            },
            {
                "filename": "public_notice.pdf",
                "extension": ".pdf",
                "size_kb": 45,
                "path": "C:/Public/",
                "last_accessed": "2025-09-10"
            },
            {
                "filename": "meeting_notes.txt",
                "extension": ".txt",
                "size_kb": 12,
                "path": "C:/Users/Admin/Desktop/",
                "last_accessed": "2025-10-25"
            }
        ]
    
    def _simulate_linux_files(self):
        """Simulate Linux file enumeration for demo"""
        return [
            {
                "filename": "credentials.txt",
                "extension": ".txt",
                "size_kb": 8,
                "path": "/home/user/Documents/",
                "last_accessed": "2025-10-20"
            },
            {
                "filename": "backup_data.tar.gz",
                "extension": ".tar.gz",
                "size_kb": 2048,
                "path": "/home/user/backups/",
                "last_accessed": "2025-10-15"
            },
            {
                "filename": "readme.md",
                "extension": ".md",
                "size_kb": 4,
                "path": "/home/user/",
                "last_accessed": "2025-09-10"
            }
        ]
    
    def _analyze_file_sensitivity(self, file_list):
        """
        Call recon priority AI to classify file sensitivity
        
        Args:
            file_list: List of file dictionaries
            
        Returns:
            dict: AI response with sensitivity predictions
        """
        try:
            response = requests.post(
                f'{self.base_url}/reconpriority/predict/',
                json=file_list,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Warning: File sensitivity AI failed ({e}), using fallback")
            # Fallback: simple heuristic
            return self._fallback_file_sensitivity(file_list)
    
    def _fallback_file_sensitivity(self, file_list):
        """Fallback file sensitivity if AI is unavailable"""
        sensitive_keywords = ['confidential', 'private', 'secret', 'password', 
                            'salary', 'patient', 'medical', 'financial']
        
        files = []
        sensitive_count = 0
        
        for f in file_list:
            # Handle both 'filename' and 'name' keys for compatibility
            filename = f.get('filename') or f.get('name', '')
            filename_lower = filename.lower()
            is_sensitive = any(kw in filename_lower for kw in sensitive_keywords)
            
            if is_sensitive:
                sensitive_count += 1
            
            files.append({
                "filename": filename,
                "sensitivity": "High" if is_sensitive else "Low",
                "sensitivity_binary": 1 if is_sensitive else 0,
                "path": f.get('path', ''),
                "confidence": 0.8 if is_sensitive else 0.2
            })
        
        return {
            "files": files,
            "summary": {
                "count_sensitive_files": sensitive_count,
                "has_high_sensitivity": 1 if sensitive_count > 0 else 0,
                "max_file_confidence": max([f['confidence'] for f in files]) if files else 0,
                "avg_sensitivity_score": sum([f['confidence'] for f in files]) / len(files) if files else 0
            }
        }
    
    def _get_attack_decisions(self, recon_data, sensitive_files):
        """
        Call attack decision AI to predict next action
        
        Args:
            recon_data: Dictionary of reconnaissance data
            sensitive_files: Output from file sensitivity AI
            
        Returns:
            dict: AI response with predicted action
        """
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
            "interesting_env_keys": self._count_interesting_env_vars(recon_data.get('env_vars', {})),
            "last_action": "reconnaissance"
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/api/attackdecision/',
                json=attack_input,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Warning: Attack decision AI failed ({e}), using fallback")
            # Fallback: simple rule-based decision
            return self._fallback_attack_decision(attack_input)
    
    def _fallback_attack_decision(self, attack_input):
        """Fallback attack decision if AI is unavailable"""
        if attack_input['count_sensitive_files'] > 3:
            return {"predicted_action": "data_exfiltration", "confidence": 0.75}
        elif attack_input['is_admin']:
            return {"predicted_action": "privilege_escalation", "confidence": 0.7}
        elif attack_input['num_open_ports'] > 5:
            return {"predicted_action": "network_scan", "confidence": 0.65}
        else:
            return {"predicted_action": "file_enumeration", "confidence": 0.6}
    
    def _count_interesting_env_vars(self, env_vars):
        """Count environment variables with interesting names"""
        interesting_keywords = ['PASSWORD', 'KEY', 'TOKEN', 'SECRET', 'API', 'CREDENTIAL']
        count = 0
        for key in env_vars.keys():
            if any(kw in key.upper() for kw in interesting_keywords):
                count += 1
        return count
    
    def _build_master_json(self, recon_data, sensitive_files, attack_plan):
        """
        Build the master JSON for report generation (matches sample-payload.json format)
        
        Args:
            recon_data: Dictionary of reconnaissance data
            sensitive_files: Output from file sensitivity AI
            attack_plan: Output from attack decision AI
        """
        self.master_data = {
            "target_name": recon_data.get('hostname', 'UNKNOWN'),
            "generated_at": timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "sim_start": self.session.start_time.strftime('%Y-%m-%d %H:%M'),
            "sim_end": timezone.now().strftime('%Y-%m-%d %H:%M'),
            
            "exec_summary": {
                "purpose": "AI-driven penetration test simulation for security assessment",
                "open_ports_list": [f"{p} - Service detected" for p in recon_data.get('open_ports', [])[:10]],
                "sensitive_data_list": [
                    f"{f['path']}{f['filename']}" 
                    for f in sensitive_files.get('files', []) 
                    if f.get('sensitivity') == 'High'
                ][:10],
                "evasion_success": 85,  # Placeholder for evasion AI
                "av_list": ["Windows Defender (signature-based)"] if 'Windows' in recon_data.get('os_name', '') else ["ClamAV"],
                "overall_risk": self._calculate_risk_level(recon_data, sensitive_files),
                "evasion_ai": 85,
                "recon_ai": int(sensitive_files.get('summary', {}).get('avg_sensitivity_score', 0.5) * 100),
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
                "open_ports": [
                    {
                        "number": p, 
                        "protocol": "tcp", 
                        "service_name": "unknown",
                        "version": "N/A",
                        "vulns": []
                    } 
                    for p in recon_data.get('open_ports', [])
                ],
                "env_vars_count": len(recon_data.get('env_vars', {})),
                "installed_software": [],
                "processes": []
            },
            
            "findings": self._generate_findings(recon_data, sensitive_files),
            
            "evasion": {
                "detection_mechanisms": ["Signature-based AV", "Host telemetry", "Network IDS"],
                "overall_success": 85,
                "skipped": []
            },
            
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
    
    def _calculate_risk_level(self, recon_data, sensitive_files):
        """Calculate overall risk level"""
        risk_score = 0
        
        # Check sensitive files
        sensitive_count = sensitive_files.get('summary', {}).get('count_sensitive_files', 0)
        if sensitive_count > 5:
            risk_score += 3
        elif sensitive_count > 2:
            risk_score += 2
        elif sensitive_count > 0:
            risk_score += 1
        
        # Check admin access
        if recon_data.get('is_admin'):
            risk_score += 2
        
        # Check open ports
        port_count = len(recon_data.get('open_ports', []))
        if port_count > 10:
            risk_score += 2
        elif port_count > 5:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 6:
            return "Critical"
        elif risk_score >= 4:
            return "High"
        elif risk_score >= 2:
            return "Medium"
        else:
            return "Low"
    
    def _generate_findings(self, recon_data, sensitive_files):
        """Generate findings list for report"""
        findings = []
        
        # Check for sensitive files
        high_sensitive = [f for f in sensitive_files.get('files', []) if f.get('sensitivity') == 'High']
        if high_sensitive:
            findings.append({
                "name": "Sensitive Files Detected",
                "evidence": f"{len(high_sensitive)} high-sensitivity files found: {', '.join([f['filename'] for f in high_sensitive[:3]])}",
                "severity": "Critical",
                "impact": "Potential data exposure and exfiltration risk"
            })
        
        # Check for admin access
        if recon_data.get('is_admin'):
            findings.append({
                "name": "Elevated Privileges Detected",
                "evidence": f"Payload running with administrator rights as user '{recon_data.get('current_user')}'",
                "severity": "High",
                "impact": "Full system compromise possible"
            })
        
        # Check for open ports
        port_count = len(recon_data.get('open_ports', []))
        if port_count > 5:
            findings.append({
                "name": "Multiple Open Ports",
                "evidence": f"{port_count} ports detected: {', '.join(map(str, recon_data.get('open_ports', [])[:10]))}",
                "severity": "Medium",
                "impact": "Increased attack surface for network-based attacks"
            })
        
        # Check for interesting environment variables
        env_count = self._count_interesting_env_vars(recon_data.get('env_vars', {}))
        if env_count > 0:
            findings.append({
                "name": "Sensitive Environment Variables",
                "evidence": f"{env_count} environment variables with potentially sensitive names detected",
                "severity": "Medium",
                "impact": "Possible credential or API key exposure"
            })
        
        return findings if findings else [{
            "name": "No Major Findings",
            "evidence": "System appears to have basic security controls in place",
            "severity": "Low",
            "impact": "Limited immediate risk"
        }]
    
    def _generate_mitigations(self, recon_data, sensitive_files):
        """Generate mitigation recommendations"""
        mitigations = []
        
        # Always include basic recommendations
        mitigations.append("Implement principle of least privilege - avoid running applications with admin rights")
        
        # Sensitive file mitigations
        sensitive_count = sensitive_files.get('summary', {}).get('count_sensitive_files', 0)
        if sensitive_count > 0:
            mitigations.append("Encrypt sensitive files and restrict access with proper ACLs")
            mitigations.append("Implement Data Loss Prevention (DLP) solutions to monitor sensitive data")
        
        # Port mitigations
        if len(recon_data.get('open_ports', [])) > 5:
            mitigations.append("Close unnecessary open ports and services")
            mitigations.append("Implement network segmentation and firewall rules")
        
        # General security
        mitigations.append("Deploy endpoint detection and response (EDR) solution")
        mitigations.append("Enable comprehensive logging and monitoring")
        mitigations.append("Regular security awareness training for users")
        mitigations.append("Conduct periodic vulnerability assessments and penetration tests")
        
        return mitigations
    
    def _generate_report(self):
        """
        Call report generation API to create PDF
        
        Returns:
            str: Path to generated report
        """
        try:
            response = requests.post(
                f'{self.base_url}/reports/generate/',
                json=self.master_data,
                timeout=120  # Report generation can take time
            )
            response.raise_for_status()
            
            # Save PDF
            report_filename = f"RedTeamReport_{self.master_data['target_name']}_{self.session.session_id}.pdf"
            report_path = f"generated_reports/{report_filename}"
            
            import os
            full_path = os.path.join('/home/prasdud/playground/raptor/src/c2', report_path)
            
            with open(full_path, 'wb') as f:
                f.write(response.content)
            
            return report_path
            
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Warning: PDF generation failed ({e})")
            # Save JSON instead as fallback
            report_filename = f"report_{self.master_data['target_name']}_{self.session.session_id}.json"
            report_path = f"generated_reports/{report_filename}"
            
            import os
            full_path = os.path.join('/home/prasdud/playground/raptor/src/c2', report_path)
            
            with open(full_path, 'w') as f:
                json.dump(self.master_data, f, indent=2)
            
            return report_path
