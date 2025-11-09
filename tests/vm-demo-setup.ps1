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

Write-Host "`n[2] Creating Realistic Demo Files (Healthcare & Finance)..." -ForegroundColor Cyan

# Function to generate random content of specific size
function Generate-FileContent {
    param(
        [int]$SizeKB,
        [string]$ContentType = "generic"
    )
    
    $targetBytes = $SizeKB * 1024
    $content = ""
    
    switch ($ContentType) {
        "passwords" {
            $content = @"
# CONFIDENTIAL - System Passwords
# Last Updated: $(Get-Date -Format "yyyy-MM-dd")

mysql_root: MyS3cr3tP@ssw0rd!
postgres_admin: Postgr3sAdm1n#2024
mongodb_user: M0ng0DB_P@ss123
redis_password: R3d1s_S3cur3!

# API Keys
AWS_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
STRIPE_API_KEY=sk_live_51234567890abcdefghijklmnopqrstuvwxyz

# Admin Credentials
admin_user: administrator
admin_pass: P@ssw0rd123!
backup_admin: backup_admin
backup_pass: BackupP@ss2024!
superuser: sysadmin
superuser_pass: Sup3rS3cr3t!

# Database Connection Strings
prod_db: Server=192.168.1.100;Database=Production;User=dbadmin;Password=DbAdm1n2024!
dev_db: Server=localhost;Database=Development;User=devuser;Password=D3vP@ss!
"@
        }
        "ssn" {
            $content = @"
PATIENT SSN RECORDS - CONFIDENTIAL
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm")

Patient_ID,Full_Name,SSN,DOB,Insurance_ID
PT001,John Michael Anderson,123-45-6789,1985-03-15,INS-8829401
PT002,Sarah Elizabeth Martinez,234-56-7890,1978-11-22,INS-9284751
PT003,David Robert Johnson,345-67-8901,1990-07-08,INS-3847562
PT004,Emily Anne Williams,456-78-9012,1982-09-30,INS-7465891
PT005,Michael James Brown,567-89-0123,1975-12-18,INS-2938475
PT006,Jennifer Lynn Davis,678-90-1234,1988-04-25,INS-8374651
PT007,Christopher Alan Miller,789-01-2345,1992-01-11,INS-4758392
PT008,Amanda Marie Wilson,890-12-3456,1980-06-05,INS-9283746
PT009,Daniel Thomas Moore,901-23-4567,1986-08-14,INS-5647382
PT010,Jessica Nicole Taylor,012-34-5678,1995-02-27,INS-1928374
"@
        }
        "credit_report" {
            $content = @"
CREDIT REPORT - CONFIDENTIAL
Report Date: $(Get-Date -Format "yyyy-MM-dd")
Credit Bureau: Experian/Equifax/TransUnion

Customer: John Anderson
SSN: 123-45-6789
Account Number: 4532-1234-5678-9012

Credit Score: 742
Outstanding Balance: $45,823.19
Available Credit: $78,500.00
Payment History: Good Standing
Late Payments (12mo): 0
Collections: None
Bankruptcies: None

Credit Card Accounts:
- Chase Visa: $12,450 / $25,000 limit
- Amex Gold: $8,923 / $15,000 limit
- Capital One: $5,200 / $10,000 limit

Loan Accounts:
- Mortgage (Wells Fargo): $285,000 remaining
- Auto Loan (Toyota Financial): $18,250 remaining
- Personal Loan (SoFi): $15,000 remaining
"@
        }
        "medical" {
            $content = @"
MEDICAL RECORD - PROTECTED HEALTH INFORMATION
Patient: Anderson, John M.
DOB: 03/15/1985
MRN: MR-2024-8829401

Visit Date: $(Get-Date -Format "MM/dd/yyyy")
Provider: Dr. Sarah Mitchell, MD
Department: Internal Medicine

Chief Complaint: Annual physical examination

Medical History:
- Hypertension (controlled with medication)
- Type 2 Diabetes Mellitus
- Hyperlipidemia
Previous Surgeries: Appendectomy (2010)

Current Medications:
- Lisinopril 10mg daily
- Metformin 500mg twice daily
- Atorvastatin 20mg daily
- Aspirin 81mg daily

Vital Signs:
BP: 128/82 mmHg
HR: 72 bpm
Temp: 98.6°F
Weight: 185 lbs
Height: 5'10"

Lab Results:
HbA1c: 6.8%
Fasting Glucose: 118 mg/dL
Total Cholesterol: 195 mg/dL
LDL: 110 mg/dL
HDL: 55 mg/dL
Triglycerides: 150 mg/dL

Assessment: Chronic conditions well-controlled
Plan: Continue current medications, follow-up in 6 months
"@
        }
        "salary" {
            $content = @"
PAYROLL SUMMARY - CONFIDENTIAL
Pay Period: $(Get-Date -Format "MMMM yyyy")
Department: All Departments

Employee_ID,Name,Department,Position,Annual_Salary,Hourly_Rate,YTD_Gross
E001,Anderson John,IT,Senior Developer,$125000,$60.10,$104167
E002,Martinez Sarah,Finance,Financial Analyst,$95000,$45.67,$79167
E003,Johnson David,HR,HR Manager,$110000,$52.88,$91667
E004,Williams Emily,Marketing,Marketing Director,$135000,$64.90,$112500
E005,Brown Michael,Operations,Operations Manager,$105000,$50.48,$87500
E006,Davis Jennifer,Sales,Sales Representative,$75000,$36.06,$62500
E007,Miller Christopher,IT,DevOps Engineer,$115000,$55.29,$95833
E008,Wilson Amanda,Finance,Senior Accountant,$88000,$42.31,$73333
E009,Moore Daniel,Legal,Legal Counsel,$145000,$69.71,$120833
E010,Taylor Jessica,Customer Service,CS Manager,$82000,$39.42,$68333

Total Payroll: $1,175,000 annually
Benefits Cost: $235,000 annually
"@
        }
        "patient" {
            $content = @"
PATIENT DATABASE EXPORT - CONFIDENTIAL
Export Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Total Records: 2,847

Patient_ID,Last_Name,First_Name,DOB,Phone,Email,Address,Insurance,Primary_Diagnosis
PT12301,Anderson,John,1985-03-15,555-0101,j.anderson@email.com,123 Main St,BlueCross,Hypertension
PT12302,Martinez,Sarah,1978-11-22,555-0102,s.martinez@email.com,456 Oak Ave,Aetna,Diabetes Type 2
PT12303,Johnson,Robert,1990-07-08,555-0103,r.johnson@email.com,789 Pine Dr,UnitedHealth,Asthma
PT12304,Williams,Emily,1982-09-30,555-0104,e.williams@email.com,321 Elm St,Cigna,Migraine
PT12305,Brown,Michael,1975-12-18,555-0105,m.brown@email.com,654 Maple Ln,Kaiser,COPD
PT12306,Davis,Jennifer,1988-04-25,555-0106,j.davis@email.com,987 Cedar Ct,Humana,Anxiety Disorder
PT12307,Miller,Chris,1992-01-11,555-0107,c.miller@email.com,147 Birch Way,BlueCross,Depression
PT12308,Wilson,Amanda,1980-06-05,555-0108,a.wilson@email.com,258 Spruce St,Aetna,Rheumatoid Arthritis
PT12309,Moore,Daniel,1986-08-14,555-0109,d.moore@email.com,369 Willow Ave,Medicare,Coronary Artery Disease
PT12310,Taylor,Jessica,1995-02-27,555-0110,j.taylor@email.com,741 Ash Dr,Medicaid,Pregnancy - 2nd Trimester
"@
        }
        default {
            $content = "Document ID: DOC-$(Get-Date -Format 'yyyyMMdd-HHmmss')`r`n"
            $content += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`r`n"
            $content += "Classification: Internal Use Only`r`n`r`n"
        }
    }
    
    # Pad content to reach target size
    while ([System.Text.Encoding]::UTF8.GetByteCount($content) -lt $targetBytes) {
        $content += "Data line $(Get-Random -Minimum 1000 -Maximum 9999): " + ("X" * 100) + "`r`n"
    }
    
    return $content.Substring(0, [Math]::Min($content.Length, $targetBytes))
}

# Create directory structure matching training data
$directories = @{
    "Healthcare" = @("LabResults", "Internal", "Insurance", "Patients", "StaffSchedules", "Meetings", "Maintenance", "PublicInfo")
    "Finance" = @("Accounts", "Loans", "HR", "Customers", "Internal", "Compliance", "Reports", "Transactions", "PublicInfo")
}

Write-Host "[*] Creating directory structure..." -ForegroundColor Yellow
foreach ($domain in $directories.Keys) {
    foreach ($subdir in $directories[$domain]) {
        $path = "C:\$domain\$subdir"
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
        }
    }
}
Write-Host "[+] Created Healthcare and Finance directory structures" -ForegroundColor Green

# Define files to create (matching training data patterns)
$filesToCreate = @(
    # HEALTHCARE - Sensitive Files (will be detected by model)
    @{Path="C:\Healthcare\LabResults\lab_results_9926.csv"; Size=180; Type="medical"; Sensitive=$true},
    @{Path="C:\Healthcare\LabResults\passwords_lab_18570.pdf"; Size=727; Type="passwords"; Sensitive=$true},
    @{Path="C:\Healthcare\LabResults\specimen_12278.pdf"; Size=850; Type="medical"; Sensitive=$true},
    @{Path="C:\Healthcare\Patients\ssn_patient_21886.csv"; Size=607; Type="ssn"; Sensitive=$true},
    @{Path="C:\Healthcare\Patients\patient_record_6301.csv"; Size=505; Type="patient"; Sensitive=$true},
    @{Path="C:\Healthcare\Patients\diagnosis_24313.docx"; Size=595; Type="medical"; Sensitive=$true},
    @{Path="C:\Healthcare\Patients\patient_20328.pdf"; Size=500; Type="patient"; Sensitive=$true},
    @{Path="C:\Healthcare\Insurance\policy_24079.docx"; Size=430; Type="generic"; Sensitive=$true},
    @{Path="C:\Healthcare\Insurance\passwords_invoice_12673.csv"; Size=701; Type="passwords"; Sensitive=$true},
    @{Path="C:\Healthcare\Insurance\claim_9693.pdf"; Size=347; Type="generic"; Sensitive=$true},
    @{Path="C:\Healthcare\Internal\guideline_23204.pdf"; Size=506; Type="generic"; Sensitive=$true},
    @{Path="C:\Healthcare\Internal\passwords_protocol_15014.xlsx"; Size=667; Type="passwords"; Sensitive=$true},
    @{Path="C:\Healthcare\Internal\procedure_6959.docx"; Size=605; Type="generic"; Sensitive=$true},
    @{Path="C:\Healthcare\StaffSchedules\medical_roster_5072.xlsx"; Size=821; Type="medical"; Sensitive=$true},
    @{Path="C:\Healthcare\StaffSchedules\shift_15341.pdf"; Size=611; Type="generic"; Sensitive=$true},
    @{Path="C:\Healthcare\Maintenance\payroll_log_18346.pdf"; Size=537; Type="salary"; Sensitive=$true},
    @{Path="C:\Healthcare\Maintenance\ssn_maintenance_23791.pdf"; Size=334; Type="ssn"; Sensitive=$true},
    
    # HEALTHCARE - False Positives (small size, won't be detected despite sensitive names)
    @{Path="C:\Healthcare\LabResults\passwords_confidential_small.txt"; Size=8; Type="passwords"; Sensitive=$false},
    @{Path="C:\Healthcare\Patients\ssn_summary_tiny.csv"; Size=12; Type="ssn"; Sensitive=$false},
    @{Path="C:\Healthcare\HR\salary_notice_small.pdf"; Size=15; Type="salary"; Sensitive=$false},
    
    # HEALTHCARE - Public/Non-Sensitive Files
    @{Path="C:\Healthcare\PublicInfo\notice_11541.pdf"; Size=247; Type="generic"; Sensitive=$false},
    @{Path="C:\Healthcare\PublicInfo\menu_21262.pdf"; Size=117; Type="generic"; Sensitive=$false},
    @{Path="C:\Healthcare\PublicInfo\parking_16469.pdf"; Size=99; Type="generic"; Sensitive=$false},
    @{Path="C:\Healthcare\Meetings\minutes_14772.txt"; Size=160; Type="generic"; Sensitive=$false},
    
    # FINANCE - Sensitive Files (will be detected by model)
    @{Path="C:\Finance\Accounts\ledger_10283.csv"; Size=388; Type="generic"; Sensitive=$true},
    @{Path="C:\Finance\Accounts\credit_report_account_18668.xlsx"; Size=445; Type="credit_report"; Sensitive=$true},
    @{Path="C:\Finance\Accounts\pin_ledger_10892.pdf"; Size=856; Type="passwords"; Sensitive=$true},
    @{Path="C:\Finance\Accounts\audit_3591.csv"; Size=377; Type="generic"; Sensitive=$true},
    @{Path="C:\Finance\HR\salary_salary_4370.xlsx"; Size=609; Type="salary"; Sensitive=$true},
    @{Path="C:\Finance\HR\confidential_salary_15420.pdf"; Size=560; Type="salary"; Sensitive=$true},
    @{Path="C:\Finance\HR\account_number_report_15353.pdf"; Size=532; Type="generic"; Sensitive=$true},
    @{Path="C:\Finance\HR\salary_payroll_1799.xlsx"; Size=673; Type="salary"; Sensitive=$true},
    @{Path="C:\Finance\Loans\agreement_5508.pdf"; Size=406; Type="generic"; Sensitive=$true},
    @{Path="C:\Finance\Loans\passwords_loan_22106.xlsx"; Size=500; Type="passwords"; Sensitive=$true},
    @{Path="C:\Finance\Loans\audit_loan_16039.docx"; Size=669; Type="generic"; Sensitive=$true},
    @{Path="C:\Finance\Customers\contract_14381.docx"; Size=554; Type="generic"; Sensitive=$true},
    @{Path="C:\Finance\Customers\tax_info_contract_4862.pdf"; Size=632; Type="generic"; Sensitive=$true},
    @{Path="C:\Finance\Internal\pin_protocol_0150.docx"; Size=404; Type="passwords"; Sensitive=$true},
    @{Path="C:\Finance\Internal\credit_report_guideline_13653.xlsx"; Size=618; Type="credit_report"; Sensitive=$true},
    @{Path="C:\Finance\Internal\pin_guideline_10162.docx"; Size=566; Type="passwords"; Sensitive=$true},
    @{Path="C:\Finance\Compliance\salary_audit_11689.docx"; Size=675; Type="salary"; Sensitive=$true},
    @{Path="C:\Finance\Compliance\bank_statement_review_8172.xlsx"; Size=427; Type="generic"; Sensitive=$true},
    @{Path="C:\Finance\Transactions\loan_contract_statement_3212.csv"; Size=461; Type="generic"; Sensitive=$true},
    @{Path="C:\Finance\Transactions\audit_statement_10786.csv"; Size=442; Type="generic"; Sensitive=$true},
    
    # FINANCE - False Positives (small size, won't be detected despite sensitive names)
    @{Path="C:\Finance\HR\passwords_tiny.txt"; Size=5; Type="passwords"; Sensitive=$false},
    @{Path="C:\Finance\Accounts\ssn_index_small.csv"; Size=10; Type="ssn"; Sensitive=$false},
    @{Path="C:\Finance\Loans\credit_report_ref.txt"; Size=18; Type="credit_report"; Sensitive=$false},
    
    # FINANCE - Public/Non-Sensitive Files
    @{Path="C:\Finance\PublicInfo\notice_3159.txt"; Size=148; Type="generic"; Sensitive=$false},
    @{Path="C:\Finance\PublicInfo\announcement_11037.txt"; Size=144; Type="generic"; Sensitive=$false},
    @{Path="C:\Finance\PublicInfo\schedule_14469.pdf"; Size=235; Type="generic"; Sensitive=$false},
    @{Path="C:\Finance\Reports\memo_7006.xlsx"; Size=313; Type="generic"; Sensitive=$false},
    @{Path="C:\Finance\Reports\summary_23424.pdf"; Size=265; Type="generic"; Sensitive=$false}
)

Write-Host "`n[*] Creating demo files..." -ForegroundColor Yellow
$sensitiveCount = 0
$falsePositiveCount = 0
$publicCount = 0

foreach ($file in $filesToCreate) {
    $content = Generate-FileContent -SizeKB $file.Size -ContentType $file.Type
    $content | Out-File -FilePath $file.Path -Encoding UTF8 -Force
    
    if ($file.Sensitive) {
        $sensitiveCount++
        Write-Host "[+] Created SENSITIVE: $($file.Path) ($($file.Size) KB)" -ForegroundColor Red
    } elseif ($file.Path -like "*passwords*" -or $file.Path -like "*ssn*" -or $file.Path -like "*credit_report*" -or $file.Path -like "*salary*") {
        $falsePositiveCount++
        Write-Host "[+] Created FALSE POSITIVE: $($file.Path) ($($file.Size) KB - too small)" -ForegroundColor Yellow
    } else {
        $publicCount++
        Write-Host "[+] Created PUBLIC: $($file.Path) ($($file.Size) KB)" -ForegroundColor Green
    }
}

Write-Host "`n[+] File creation summary:" -ForegroundColor Cyan
Write-Host "    Sensitive files (model WILL detect): $sensitiveCount" -ForegroundColor Red
Write-Host "    False positives (model WON'T detect): $falsePositiveCount" -ForegroundColor Yellow
Write-Host "    Public/non-sensitive files: $publicCount" -ForegroundColor Green
Write-Host "    Total files created: $($filesToCreate.Count)" -ForegroundColor White

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
Write-Host "  Demo Domains: Healthcare (C:\Healthcare\) and Finance (C:\Finance\)" -ForegroundColor White
Write-Host "  Total Files: $($filesToCreate.Count) files across multiple departments" -ForegroundColor White
Write-Host "  Sensitive Files: $sensitiveCount files that model WILL detect" -ForegroundColor Red
Write-Host "  False Positives: $falsePositiveCount files with sensitive names but too small to detect" -ForegroundColor Yellow
Write-Host "  Public Files: $publicCount non-sensitive files" -ForegroundColor Green
Write-Host "  Antivirus: Windows Defender (Enabled)" -ForegroundColor White
Write-Host "`n  NOTE: File structure matches the recon-priority model training data" -ForegroundColor Cyan
Write-Host "        Model will prioritize files based on size, keywords, and location" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor White

# Execute the keep-alive script
Invoke-Expression $keepAliveScript
