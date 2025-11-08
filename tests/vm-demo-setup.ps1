# VM Demo Setup Script
# This script initializes a Windows VM to simulate a realistic environment for penetration testing demonstrations
# Run as Administrator

Write-Host "=== RAPTOR Demo Environment Setup ===" -ForegroundColor Cyan
Write-Host "This script will set up services, ports, and processes for demonstration purposes`n" -ForegroundColor Yellow

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    exit 1
}

# Function to create a listening port
function Start-ListeningPort {
    param(
        [int]$Port,
        [string]$Description
    )
    
    try {
        $endpoint = New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Any, $Port)
        $listener = New-Object System.Net.Sockets.TcpListener $endpoint
        $listener.Start()
        Write-Host "[+] Started listener on port $Port ($Description)" -ForegroundColor Green
        return $listener
    } catch {
        Write-Host "[-] Failed to start port $Port : $_" -ForegroundColor Red
        return $null
    }
}

# Array to store listeners (so they don't get garbage collected)
$global:listeners = @()

Write-Host "`n[1] Opening Common Ports..." -ForegroundColor Cyan

# Web Server (HTTP)
$global:listeners += Start-ListeningPort -Port 80 -Description "HTTP Web Server"

# Web Server (HTTPS)
$global:listeners += Start-ListeningPort -Port 443 -Description "HTTPS Web Server"

# MySQL Database
$global:listeners += Start-ListeningPort -Port 3306 -Description "MySQL Database"

# PostgreSQL Database
$global:listeners += Start-ListeningPort -Port 5432 -Description "PostgreSQL Database"

# Jenkins CI/CD
$global:listeners += Start-ListeningPort -Port 8080 -Description "Jenkins CI/CD"

# MongoDB
$global:listeners += Start-ListeningPort -Port 27017 -Description "MongoDB"

# Redis
$global:listeners += Start-ListeningPort -Port 6379 -Description "Redis"

# Elasticsearch
$global:listeners += Start-ListeningPort -Port 9200 -Description "Elasticsearch"

# SSH (if OpenSSH is installed)
$global:listeners += Start-ListeningPort -Port 22 -Description "SSH Server"

# FTP
$global:listeners += Start-ListeningPort -Port 21 -Description "FTP Server"

# SMB is already running on Windows, but we can note it
Write-Host "[+] SMB ports 445, 139 should already be open (Windows default)" -ForegroundColor Green

# RDP is typically running, but let's ensure it
Write-Host "[+] RDP port 3389 should already be open (Windows default)" -ForegroundColor Green

Write-Host "`n[2] Creating Sensitive Files..." -ForegroundColor Cyan

# Create directories
$sensitiveDir = "C:\SensitiveData"
$credentialsDir = "C:\Credentials"
$sshDir = "$env:USERPROFILE\.ssh"

@($sensitiveDir, $credentialsDir, $sshDir) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
        Write-Host "[+] Created directory: $_" -ForegroundColor Green
    }
}

# passwords.txt
@"
# Production Database Passwords
mysql_root: MyS3cr3tP@ssw0rd!
postgres_admin: Postgr3sAdm1n#2024
mongodb_user: M0ng0DB_P@ss123

# API Keys
AWS_ACCESS_KEY=XXXXXXXXXXX
AWS_SECRET_KEY=XXXXXXXXXXX
STRIPE_API_KEY=XXXXXXXXXXX

# Admin Credentials
admin_user: administrator
admin_pass: P@ssw0rd123!
backup_admin: backup_admin
backup_pass: BackupP@ss2024!
"@ | Out-File -FilePath "$sensitiveDir\passwords.txt" -Encoding ASCII
Write-Host "[+] Created $sensitiveDir\passwords.txt" -ForegroundColor Green

# database_credentials.txt
@"
[Production Database]
Host: db.production.internal
Port: 3306
Username: prod_user
Password: Pr0dDB_2024!
Database: production_db

[Development Database]
Host: localhost
Port: 5432
Username: dev_user
Password: D3v_P@ssw0rd
Database: dev_db
"@ | Out-File -FilePath "$credentialsDir\database_credentials.txt" -Encoding ASCII
Write-Host "[+] Created $credentialsDir\database_credentials.txt" -ForegroundColor Green

# api_keys.json
@"
{
  "stripe": {
    "public_key": "XXXXXXXXXXX",
    "secret_key": "XXXXXXXXXXX"
  },
  "aws": {
    "access_key_id": "XXXXXXXXXXX",
    "secret_access_key": "XXXXXXXXXXX",
    "region": "us-east-1"
  },
  "github": {
    "token": "XXXXXXXXXXX",
    "username": "admin"
  },
  "slack": {
    "webhook_url": "XXXXXXXXXXX",
    "bot_token": "XXXXXXXXXXX"
  }
}
"@ | Out-File -FilePath "$sensitiveDir\api_keys.json" -Encoding ASCII
Write-Host "[+] Created $sensitiveDir\api_keys.json" -ForegroundColor Green

# SSH private key
@"
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
NhAAAAAwEAAQAAAYEA1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP
QRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
[... truncated for brevity - this is a fake key ...]
-----END OPENSSH PRIVATE KEY-----
"@ | Out-File -FilePath "$sshDir\id_rsa" -Encoding ASCII
Write-Host "[+] Created $sshDir\id_rsa (SSH private key)" -ForegroundColor Green

# config files with credentials
@"
[default]
aws_access_key_id = XXXXXXXXXXX
aws_secret_access_key = XXXXXXXXXXX
region = us-east-1
"@ | Out-File -FilePath "$env:USERPROFILE\.aws\credentials" -Encoding ASCII -Force
Write-Host "[+] Created AWS credentials file" -ForegroundColor Green

# .env file
@"
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=MyS3cr3tP@ssw0rd!
DB_NAME=production

JWT_SECRET=XXXXXXXXXXX
API_KEY=XXXXXXXXXXX
STRIPE_SECRET=XXXXXXXXXXX

ADMIN_EMAIL=admin@company.com
ADMIN_PASSWORD=@dm1nP@ss2024!
"@ | Out-File -FilePath "C:\Projects\.env" -Encoding ASCII -Force
Write-Host "[+] Created C:\Projects\.env" -ForegroundColor Green

Write-Host "`n[3] Starting Background Processes..." -ForegroundColor Cyan

# Simulate running services/applications
# These will show up in the process list

# Start notepad instances (harmless but visible)
Start-Process notepad.exe -WindowStyle Minimized
Start-Process notepad.exe -WindowStyle Minimized
Write-Host "[+] Started background processes" -ForegroundColor Green

# Create a script that will keep running
$keepAliveScript = @"
# Keep the ports alive
Write-Host 'Demo environment is running. Press Ctrl+C to stop.' -ForegroundColor Yellow
Write-Host 'Open ports: 21, 22, 80, 443, 3306, 5432, 6379, 8080, 9200, 27017' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Sensitive files created in:' -ForegroundColor Cyan
Write-Host '  - C:\SensitiveData' -ForegroundColor White
Write-Host '  - C:\Credentials' -ForegroundColor White
Write-Host '  - $env:USERPROFILE\.ssh' -ForegroundColor White
Write-Host '  - $env:USERPROFILE\.aws' -ForegroundColor White
Write-Host '  - C:\Projects\.env' -ForegroundColor White
Write-Host ''
Write-Host 'Keep this window open to maintain the demo environment.' -ForegroundColor Yellow
Write-Host ''

# Keep script running
while (`$true) {
    Start-Sleep -Seconds 30
}
"@

Write-Host "`n[4] Enabling Windows Features..." -ForegroundColor Cyan

# Enable Windows Defender (for AV detection)
try {
    Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction SilentlyContinue
    Write-Host "[+] Windows Defender enabled" -ForegroundColor Green
} catch {
    Write-Host "[!] Could not modify Windows Defender settings" -ForegroundColor Yellow
}

# Enable SMB (for network share detection)
try {
    Enable-WindowsOptionalFeature -Online -FeatureName "SMB1Protocol" -NoRestart -ErrorAction SilentlyContinue | Out-Null
    Write-Host "[+] SMB protocol enabled" -ForegroundColor Green
} catch {
    Write-Host "[!] SMB already configured" -ForegroundColor Yellow
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host "`nDemo Environment Summary:" -ForegroundColor Cyan
Write-Host "  Open Ports: 21 (FTP), 22 (SSH), 80 (HTTP), 443 (HTTPS), 445 (SMB), 3306 (MySQL), 3389 (RDP), 5432 (PostgreSQL), 6379 (Redis), 8080 (Jenkins), 9200 (Elasticsearch), 27017 (MongoDB)" -ForegroundColor White
Write-Host "  Sensitive Files: passwords.txt, database_credentials.txt, api_keys.json, id_rsa, .aws/credentials, .env" -ForegroundColor White
Write-Host "  Antivirus: Windows Defender (Enabled)" -ForegroundColor White
Write-Host "`n" -ForegroundColor White

# Execute the keep-alive script
Invoke-Expression $keepAliveScript
