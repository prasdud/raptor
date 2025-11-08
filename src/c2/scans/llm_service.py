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
        architecture = recon.get('architecture', 'Unknown')
        hostname = recon.get('hostname', 'Unknown')
        current_user = recon.get('current_user', 'Unknown')
        is_admin = recon.get('is_admin', False)
        
        # Network information
        open_ports = recon.get('open_ports', [])
        port_details = [f"Port {p.get('number', 'N/A')}/{p.get('protocol', 'tcp')}" for p in open_ports[:20]]
        network_ips = recon.get('network_ips', [])
        subnets = recon.get('subnets', [])
        firewall_info = recon.get('firewall', {})
        firewall_status = f"{firewall_info.get('name', 'Unknown')} ({'Enabled' if firewall_info.get('enabled') else 'Disabled'})"
        
        # User information
        privileged_users = recon.get('privileged_accounts', [])
        active_users = recon.get('active_users', [])
        
        # Software and processes
        installed_software = recon.get('installed_software', [])
        software_summary = "\n".join([f"  - {sw}" for sw in installed_software[:15]])
        processes_count = len(recon.get('processes', []))
        
        # Antivirus
        av_list = recon.get('active_av', [])
        av_summary = ", ".join([av.get('name', 'Unknown') for av in av_list]) if av_list else "None detected"
        
        # Findings
        findings = master_json.get('findings', [])
        findings_summary = "\n".join([
            f"  [{f.get('severity', 'Unknown')}] {f.get('name', 'Unknown')}\n    Evidence: {f.get('evidence', 'N/A')}\n    Impact: {f.get('impact', 'N/A')}"
            for f in findings[:10]
        ])
        
        # Sensitive files
        sensitive_files = master_json.get('exec_summary', {}).get('sensitive_data_list', [])
        sensitive_summary = "\n".join([f"  - {f}" for f in sensitive_files[:15]])
        
        # Attack recommendations
        attacks = master_json.get('attacks', [])
        attack_summary = "\n".join([
            f"  - {a.get('name', 'Unknown')} (Priority: {a.get('priority', 'N/A')})\n    {a.get('description', 'N/A')}"
            for a in attacks[:5]
        ])
        
        # Build comprehensive prompt
        prompt = f"""You are a senior cybersecurity consultant analyzing a penetration test report. Provide SPECIFIC, ACTIONABLE mitigations based on the EXACT findings below.

═══════════════════════════════════════════════════════════
TARGET SYSTEM PROFILE
═══════════════════════════════════════════════════════════
Hostname: {hostname}
Operating System: {os_info} ({architecture})
Current User: {current_user} (Privileged: {"YES ⚠️" if is_admin else "NO"})
Overall Risk: {risk_level}

═══════════════════════════════════════════════════════════
NETWORK & INFRASTRUCTURE
═══════════════════════════════════════════════════════════
Open Ports ({len(open_ports)} total):
{chr(10).join(["  - " + p for p in port_details]) if port_details else "  - None"}

IP Addresses: {', '.join(network_ips[:5]) if network_ips else 'N/A'}
Subnets: {', '.join(subnets[:5]) if subnets else 'N/A'}
Firewall: {firewall_status}

═══════════════════════════════════════════════════════════
USER ACCOUNTS & ACCESS CONTROL
═══════════════════════════════════════════════════════════
Privileged Accounts ({len(privileged_users)}):
{chr(10).join(["  - " + str(u) for u in privileged_users[:10]]) if privileged_users else "  - None"}

Active Users ({len(active_users)}):
{chr(10).join(["  - " + str(u) for u in active_users[:10]]) if active_users else "  - None"}

═══════════════════════════════════════════════════════════
INSTALLED SOFTWARE & SECURITY
═══════════════════════════════════════════════════════════
Antivirus/EDR: {av_summary}
Running Processes: {processes_count}

Key Installed Software:
{software_summary if software_summary else "  - N/A"}

═══════════════════════════════════════════════════════════
SECURITY FINDINGS (CRITICAL ISSUES)
═══════════════════════════════════════════════════════════
{findings_summary if findings_summary else "No major findings"}

═══════════════════════════════════════════════════════════
SENSITIVE DATA EXPOSURE
═══════════════════════════════════════════════════════════
{sensitive_summary if sensitive_summary else "No sensitive files detected"}

═══════════════════════════════════════════════════════════
AI-IDENTIFIED ATTACK VECTORS
═══════════════════════════════════════════════════════════
{attack_summary if attack_summary else "No attack vectors identified"}

═══════════════════════════════════════════════════════════
MITIGATION REQUIREMENTS
═══════════════════════════════════════════════════════════

Based on the SPECIFIC findings above, provide 8-12 TARGETED mitigations. Each mitigation MUST:

1. Reference SPECIFIC findings (e.g., "Close port 3306" not "Close unnecessary ports")
2. Include EXACT implementation steps (e.g., "Run: netsh advfirewall firewall add rule...")
3. Prioritize by severity (Critical → High → Medium → Low)
4. Address the ACTUAL OS/software found ({os_info})
5. Consider the SPECIFIC ports, users, and software identified above

Format: Return ONLY a numbered list of mitigations. Each mitigation should be 1-2 sentences maximum.

EXAMPLES OF GOOD MITIGATIONS:
✓ "Disable MySQL service on port 3306 or restrict to localhost (127.0.0.1) via firewall rule"
✓ "Implement file-level encryption for passwords.txt and api_keys.json found in C:\\SensitiveData"
✓ "Remove administrative privileges from user '{current_user}' and enforce standard user accounts"

EXAMPLES OF BAD MITIGATIONS:
✗ "Implement security best practices" (too vague)
✗ "Close unnecessary ports" (which ports?)
✗ "Improve access controls" (how specifically?)

Provide mitigations now:"""

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
        
        # Fix common character encoding issues
        # Replace ASCII codes that appear as numbers (e.g., "39;" for single quote)
        import re
        response_text = re.sub(r'(\d+);', lambda m: chr(int(m.group(1))), response_text)
        
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
