"""
LLM Service - Generates AI-powered mitigations using Cohere
"""
import os
import json
import cohere
from django.conf import settings


class LLMMitigationService:
    """Service for generating mitigations using Cohere LLM"""
    
    def __init__(self):
        """Initialize Cohere client"""
        api_key = getattr(settings, 'COHERE_API_KEY', None) or os.environ.get('COHERE_API_KEY')
        
        if not api_key:
            raise ValueError(
                "COHERE_API_KEY not found. Set it in settings.py or as environment variable."
            )
        
        self.client = cohere.Client(api_key)
    
    def generate_mitigations(self, master_json, max_tokens=2000, temperature=0.7):
        """
        Generate security mitigations based on the complete scan data
        
        Args:
            master_json (dict): Complete scan data including recon, findings, attacks
            max_tokens (int): Maximum tokens in response
            temperature (float): LLM temperature (0.0-1.0, lower = more focused)
            
        Returns:
            list: List of mitigation recommendation strings
        """
        try:
            # Build comprehensive prompt
            prompt = self._build_prompt(master_json)
            
            # Call Cohere API
            response = self.client.chat(
                message=prompt,
                model="command-r-08-2024",  # Current Cohere model (as of Oct 2025)
                temperature=temperature,
                max_tokens=max_tokens,
                preamble="""You are an elite cybersecurity engineer and penetration testing expert with deep knowledge of:
- Network security and defense-in-depth strategies
- MITRE ATT&CK framework and TTPs
- CIS Controls and security best practices
- Incident response and threat mitigation
- Enterprise security architecture

Your role is to analyze penetration test results and provide actionable, prioritized security mitigations."""
            )
            
            # Parse response into list of mitigations
            mitigations = self._parse_llm_response(response.text)
            
            return mitigations
            
        except Exception as e:
            print(f"⚠️  LLM mitigation generation failed: {e}")
            # Return fallback mitigations
            return self._get_fallback_mitigations()
    
    def _build_prompt(self, master_json):
        """
        Build detailed prompt from scan data
        
        Args:
            master_json (dict): Complete scan data
            
        Returns:
            str: Formatted prompt for LLM
        """
        # Extract key information
        target = master_json.get('target_name', 'UNKNOWN')
        risk_level = master_json.get('exec_summary', {}).get('overall_risk', 'Unknown')
        
        # Recon summary
        recon = master_json.get('recon_data', {})
        os_info = f"{recon.get('os_name', 'Unknown')} {recon.get('os_version', '')}"
        is_admin = recon.get('is_admin', False)
        open_ports = recon.get('open_ports', [])
        
        # Findings
        findings = master_json.get('findings', [])
        findings_summary = "\n".join([
            f"- [{f.get('severity', 'Unknown')}] {f.get('name', 'Unknown')}: {f.get('evidence', '')}"
            for f in findings[:10]  # Limit to top 10
        ])
        
        # Sensitive files
        sensitive_files = master_json.get('exec_summary', {}).get('sensitive_data_list', [])
        sensitive_summary = "\n".join([f"- {f}" for f in sensitive_files[:10]])
        
        # Attack recommendations
        attacks = master_json.get('attacks', [])
        attack_summary = "\n".join([
            f"- {a.get('name', 'Unknown')}: {a.get('description', '')}"
            for a in attacks[:5]
        ])
        
        # Build prompt
        prompt = f"""Analyze the following penetration test results and provide specific, actionable security mitigations.

**Target System:** {target}
**Risk Level:** {risk_level}
**Operating System:** {os_info}
**Administrative Access:** {"YES - Privileged access detected" if is_admin else "NO"}
**Open Ports:** {len(open_ports)} ports detected - {', '.join(map(str, open_ports[:15]))}

**Security Findings:**
{findings_summary if findings_summary else "No major findings"}

**Sensitive Files Identified:**
{sensitive_summary if sensitive_summary else "No sensitive files detected"}

**AI-Recommended Attack Vectors:**
{attack_summary if attack_summary else "No attack vectors identified"}

Based on this penetration test data, provide **8-12 prioritized security mitigations**. Format your response as a numbered list where each mitigation:

1. Addresses specific findings from the scan
2. Includes concrete, implementable actions
3. Prioritizes critical vulnerabilities first
4. Considers the target's OS and environment
5. Follows security best practices (CIS Controls, NIST, MITRE ATT&CK)

Focus on:
- Network hardening (firewall rules, port security)
- Access control and privilege management
- Data protection (encryption, DLP)
- Detection and monitoring (EDR, SIEM, logging)
- Vulnerability remediation
- Security awareness and training

Provide clear, concise recommendations suitable for both technical teams and management."""

        return prompt
    
    def _parse_llm_response(self, response_text):
        """
        Parse LLM response into clean list of mitigations
        
        Args:
            response_text (str): Raw LLM response
            
        Returns:
            list: List of mitigation strings
        """
        mitigations = []
        
        # Split by lines
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Remove markdown formatting
            line = line.replace('**', '').replace('*', '')
            
            # Remove numbering (e.g., "1. ", "1) ", "- ")
            if line[0:3].strip() and line[0:3].strip()[0].isdigit():
                # Numbered list: "1. mitigation" or "1) mitigation"
                parts = line.split('.', 1) if '.' in line else line.split(')', 1)
                if len(parts) > 1:
                    line = parts[1].strip()
            elif line.startswith('-') or line.startswith('•'):
                # Bullet list: "- mitigation"
                line = line[1:].strip()
            
            # Add if it's substantive (not a header or empty)
            if len(line) > 20 and not line.endswith(':'):
                mitigations.append(line)
        
        # Return up to 12 mitigations
        return mitigations[:12]
    
    def _get_fallback_mitigations(self):
        """
        Return basic mitigations if LLM fails
        
        Returns:
            list: Fallback mitigation recommendations
        """
        return [
            "Implement principle of least privilege - avoid running applications with admin rights",
            "Close unnecessary open ports and services to reduce attack surface",
            "Encrypt sensitive files at rest using full-disk encryption or file-level encryption",
            "Implement network segmentation to isolate critical systems from general network",
            "Deploy endpoint detection and response (EDR) solution for real-time threat detection",
            "Enable comprehensive logging and forward logs to a SIEM for correlation analysis",
            "Implement Data Loss Prevention (DLP) to monitor and prevent sensitive data exfiltration",
            "Regular security awareness training for all users, especially on phishing and social engineering",
            "Conduct periodic vulnerability assessments and penetration tests",
            "Establish an incident response plan and practice through tabletop exercises",
        ]
