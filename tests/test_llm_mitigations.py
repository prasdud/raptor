#!/usr/bin/env python3
"""
Test LLM Mitigation Integration

This script tests the LLM service with a sample scan dataset
"""
import sys
import os
import json

# Add Django project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/c2'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'c2.settings')

import django
django.setup()

from scans.llm_service import LLMMitigationService


def test_llm_service():
    """Test LLM mitigation generation"""
    
    print("🧪 Testing LLM Mitigation Service")
    print("=" * 50)
    print()
    
    # Sample scan data (realistic)
    test_data = {
        "target_name": "PROD-WEB-01",
        "generated_at": "2024-10-30T12:00:00Z",
        "sim_start": "2024-10-30 11:45",
        "sim_end": "2024-10-30 12:00",
        
        "exec_summary": {
            "purpose": "Quarterly security assessment",
            "open_ports_list": [
                "22 - SSH",
                "80 - HTTP",
                "443 - HTTPS",
                "3306 - MySQL",
                "8080 - Jenkins"
            ],
            "sensitive_data_list": [
                "/var/www/config/database.yml",
                "/home/admin/.ssh/id_rsa",
                "/opt/app/secrets.json",
                "/var/log/auth.log"
            ],
            "av_list": ["None detected"],
            "overall_risk": "High",
            "recon_ai": 87,
            "attack_ai": 92
        },
        
        "recon_data": {
            "os_name": "Ubuntu",
            "os_version": "22.04 LTS",
            "architecture": "x86_64",
            "hostname": "PROD-WEB-01",
            "current_user": "www-data",
            "is_admin": False,
            "open_ports": [
                {"number": 22, "protocol": "tcp", "service_name": "ssh", "version": "OpenSSH 8.9"},
                {"number": 80, "protocol": "tcp", "service_name": "http", "version": "nginx 1.22"},
                {"number": 443, "protocol": "tcp", "service_name": "https", "version": "nginx 1.22"},
                {"number": 3306, "protocol": "tcp", "service_name": "mysql", "version": "8.0.32"},
                {"number": 8080, "protocol": "tcp", "service_name": "http", "version": "Jenkins 2.387"}
            ],
        },
        
        "findings": [
            {
                "name": "MySQL Exposed to Internet",
                "evidence": "Port 3306 open and accessible externally",
                "severity": "Critical",
                "impact": "Direct database access possible, data breach risk"
            },
            {
                "name": "Jenkins Unauthenticated Access",
                "evidence": "Port 8080 allows anonymous access to CI/CD pipeline",
                "severity": "High",
                "impact": "Code injection, credential theft, supply chain attack"
            },
            {
                "name": "SSH Keys Discovered",
                "evidence": "Private SSH key found in user home directory",
                "severity": "High",
                "impact": "Lateral movement to other systems possible"
            },
            {
                "name": "Database Credentials in Plaintext",
                "evidence": "/var/www/config/database.yml contains unencrypted passwords",
                "severity": "High",
                "impact": "Database compromise if file is accessed"
            },
            {
                "name": "No Endpoint Protection",
                "evidence": "No AV/EDR detected on system",
                "severity": "Medium",
                "impact": "Malware could execute undetected"
            }
        ],
        
        "attacks": [
            {
                "name": "database_access",
                "description": "Attempt direct MySQL connection via exposed port 3306",
                "outcome": "Simulated - would succeed with brute force",
                "priority": 10
            },
            {
                "name": "jenkins_exploit",
                "description": "Exploit unauthenticated Jenkins to inject malicious pipeline",
                "outcome": "Simulated - RCE possible",
                "priority": 9
            }
        ]
    }
    
    print("📊 Test Scan Data:")
    print(f"   Target: {test_data['target_name']}")
    print(f"   Risk Level: {test_data['exec_summary']['overall_risk']}")
    print(f"   OS: {test_data['recon_data']['os_name']} {test_data['recon_data']['os_version']}")
    print(f"   Open Ports: {len(test_data['recon_data']['open_ports'])}")
    print(f"   Findings: {len(test_data['findings'])} ({test_data['findings'][0]['severity']} severity)")
    print()
    
    # Initialize LLM service
    try:
        print("🤖 Initializing LLM service...")
        llm = LLMMitigationService()
        print("   ✓ Service initialized")
        print()
    except ValueError as e:
        print(f"   ❌ API key error: {e}")
        print()
        print("To fix:")
        print("  export COHERE_API_KEY='your-key-here'")
        print("  OR set in src/c2/c2/settings.py")
        return False
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        return False
    
    # Generate mitigations
    try:
        print("⚙️  Generating mitigations...")
        print("   (This may take 5-10 seconds)")
        print()
        
        mitigations = llm.generate_mitigations(
            master_json=test_data,
            max_tokens=2000,
            temperature=0.7
        )
        
        print(f"✅ Generated {len(mitigations)} mitigations")
        print()
        print("=" * 50)
        print("📋 MITIGATIONS:")
        print("=" * 50)
        print()
        
        for i, mitigation in enumerate(mitigations, 1):
            print(f"{i}. {mitigation}")
            print()
        
        print("=" * 50)
        print()
        
        # Validate mitigations
        print("🔍 Validation:")
        
        # Check if mitigations reference specific findings
        has_mysql = any('mysql' in m.lower() or '3306' in m.lower() for m in mitigations)
        has_jenkins = any('jenkins' in m.lower() or 'ci/cd' in m.lower() for m in mitigations)
        has_ssh = any('ssh' in m.lower() for m in mitigations)
        
        print(f"   {'✓' if has_mysql else '⚠️'}  MySQL mitigation mentioned")
        print(f"   {'✓' if has_jenkins else '⚠️'}  Jenkins mitigation mentioned")
        print(f"   {'✓' if has_ssh else '⚠️'}  SSH hardening mentioned")
        print(f"   {'✓' if len(mitigations) >= 8 else '⚠️'}  Sufficient detail ({len(mitigations)} items)")
        print()
        
        if has_mysql and has_jenkins and len(mitigations) >= 8:
            print("✅ Test PASSED - LLM generated contextual mitigations!")
        else:
            print("⚠️  Test PARTIAL - Mitigations may need tuning")
        
        return True
        
    except Exception as e:
        print(f"❌ Mitigation generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_llm_service()
    sys.exit(0 if success else 1)
