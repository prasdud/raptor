#!/usr/bin/env python3
"""
finance-data-generation.py
Generate realistic synthetic finance/banking file-metadata for training Recon Priority AI.

Features:
- Realistic folder/extension correlations
- Filename keywords correlated with sensitivity
- Size/date distributions conditioned on extension & sensitivity
- Configurable class imbalance and dataset size
- Small percentage of label noise (mislabels) to simulate real data
- Outputs JSON and CSV
"""

import json
import csv
import random
import datetime
from collections import Counter

# --------------------------- CONFIG ---------------------------
NUM_ROWS = 10000
RANDOM_SEED = 42
OUTPUT_JSON = "master-finance-data.json"
OUTPUT_CSV  = "master-finance-data.csv"

TARGET_DISTRIBUTION = {
    "high": 0.15,    # sensitive contracts, customer info
    "medium": 0.30,  # reports, internal memos
    "low": 0.55      # public notices, general info
}

LABEL_NOISE_FRACTION = 0.03

FOLDERS = [
    'C:/Finance/Accounts/',
    'C:/Finance/Customers/',
    'C:/Finance/Loans/',
    'C:/Finance/Transactions/',
    'C:/Finance/HR/',
    'C:/Finance/Reports/',
    'C:/Finance/Compliance/',
    'C:/Finance/PublicInfo/Announcements/',
    'C:/Finance/PublicInfo/Guidelines/',
    'C:/Finance/Internal/Policies/'
]

EXT_BY_FOLDER = {
    'Accounts':     ['.xlsx', '.csv', '.pdf'],
    'Customers':    ['.pdf', '.docx', '.csv'],
    'Loans':        ['.pdf', '.docx', '.xls', '.xlsx'],
    'Transactions': ['.csv', '.xlsx', '.pdf'],
    'HR':           ['.docx', '.pdf', '.xlsx'],
    'Reports':      ['.pdf', '.xlsx', '.csv'],
    'Compliance':   ['.pdf', '.docx', '.xlsx'],
    'PublicInfo':   ['.pdf', '.txt', '.csv'],
    'Internal':     ['.docx', '.pdf', '.xlsx']
}

HIGH_KEYWORDS = [
    "confidential","customer","ssn","account_number","pin","loan_contract",
    "salary","audit","passwords","tax_info","credit_report","bank_statement"
]
MEDIUM_KEYWORDS = [
    "report","summary","invoice","statement","transaction","memo","analysis","ledger"
]
LOW_KEYWORDS = [
    "announcement","guidelines","policy","public_notice","menu","schedule","info"
]

DATE_START = datetime.datetime(2022, 1, 1, 0, 0, 0)
DATE_END   = datetime.datetime(2025, 12, 31, 23, 59, 59)

random.seed(RANDOM_SEED)

# ------------------------ UTILITIES ---------------------------
def weighted_choice(choices):
    total = sum(w for _, w in choices)
    r = random.random() * total
    upto = 0.0
    for item, weight in choices:
        if upto + weight >= r:
            return item
        upto += weight
    return choices[-1][0]

def folder_key(folder_path):
    parts = [p for p in folder_path.split('/') if p]
    for candidate in reversed(parts):
        if candidate in EXT_BY_FOLDER:
            return candidate
    if len(parts) >= 2:
        return parts[-2]
    return parts[-1]

def pick_extension_for_folder(folder):
    key = folder_key(folder)
    prefer = EXT_BY_FOLDER.get(key, ['.pdf', '.txt', '.csv', '.docx', '.xlsx', '.xls'])
    weights = [(ext, max(1.0, 2.0 - 0.2 * i)) for i, ext in enumerate(prefer)]
    return weighted_choice(weights)

def random_iso_date(start=DATE_START, end=DATE_END):
    delta = int((end - start).total_seconds())
    sec = random.randint(0, delta)
    dt = start + datetime.timedelta(seconds=sec)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def filesize_by_ext_and_sensitivity(ext, sensitivity):
    ext = ext.lower()
    if ext in ('.txt',):
        base = random.randint(1, 150)
    elif ext in ('.csv',):
        base = int(random.gauss(300, 250))
    elif ext in ('.xls', '.xlsx'):
        base = int(random.gauss(700, 800))
    elif ext in ('.pdf',):
        base = int(random.gauss(800, 900))
    elif ext in ('.docx',):
        base = int(random.gauss(400, 350))
    else:
        base = int(random.gauss(400, 500))
    if sensitivity == "high":
        adj = abs(int(random.gauss(1.15, 0.05) * base))
    elif sensitivity == "medium":
        adj = abs(int(random.gauss(1.0, 0.08) * base))
    else:
        adj = abs(int(random.gauss(0.85, 0.1) * base))
    return max(1, min(adj, 10_000))

def choose_sensitivity_for_row(folder, extension, filename_keywords):
    base = TARGET_DISTRIBUTION.copy()
    key = folder_key(folder)
    if key in ("Customers", "Loans", "Accounts"):
        base['high'] += 0.10
        base['low']  -= 0.06
    elif "PublicInfo" in key:
        base['low'] += 0.12
        base['high'] -= 0.06
    elif key in ("HR", "Reports", "Compliance"):
        base['low'] += 0.06
        base['medium'] += 0.02
    for kw in filename_keywords:
        if kw in HIGH_KEYWORDS:
            base['high'] += 0.15
            base['low']  -= 0.08
        elif kw in MEDIUM_KEYWORDS:
            base['medium'] += 0.05
            base['low'] -= 0.02
        elif kw in LOW_KEYWORDS:
            base['low'] += 0.08
            base['high'] -= 0.03
    for k in base:
        base[k] = max(base[k], 0.0)
    s = sum(base.values())
    if s <= 0:
        base = TARGET_DISTRIBUTION.copy()
        s = sum(base.values())
    probs = {k: v / s for k, v in base.items()}
    choices = list(probs.items())
    return weighted_choice(choices)

def generate_filename(folder, extension, idx):
    key = folder_key(folder)
    base_tokens = {
        'Accounts': ['ledger','balance','account','audit'],
        'Customers': ['customer','profile','info','contract'],
        'Loans': ['loan','agreement','repayment','contract'],
        'Transactions': ['transaction','transfer','statement','summary'],
        'HR': ['payroll','salary','roster','report'],
        'Reports': ['report','analysis','summary','memo'],
        'Compliance': ['policy','guideline','audit','review'],
        'PublicInfo': ['announcement','notice','info','schedule'],
        'Internal': ['procedure','policy','protocol','guideline']
    }
    tokens = base_tokens.get(key, [key.lower()])
    p = random.random()
    keywords = []
    if p < 0.08:
        kw = random.choice(HIGH_KEYWORDS)
        keywords.append(kw)
    elif p < 0.28:
        kw = random.choice(MEDIUM_KEYWORDS)
        keywords.append(kw)
    elif p < 0.55:
        kw = random.choice(LOW_KEYWORDS)
        keywords.append(kw)
    base = random.choice(tokens)
    filename_body = f"{base}_{idx:04d}"
    if random.random() < 0.12:
        filename_body += "_" + random.choice(['final','v2','draft','archived','confidential'])
    if keywords and random.random() < 0.9:
        filename_body = f"{keywords[0]}_{filename_body}"
    return filename_body + extension, keywords

# ------------------------ MAIN GENERATOR -----------------------
def generate_dataset(num_rows=NUM_ROWS):
    rows = []
    counts_target = {k: int(num_rows * v) for k, v in TARGET_DISTRIBUTION.items()}
    remaining = num_rows - sum(counts_target.values())
    counts_target['low'] += remaining
    for i in range(num_rows):
        folder = random.choice(FOLDERS)
        ext = pick_extension_for_folder(folder)
        fname, keywords = generate_filename(folder, ext, i)
        sensitivity = choose_sensitivity_for_row(folder, ext, keywords)
        filesize = filesize_by_ext_and_sensitivity(ext, sensitivity)
        date_modified = random_iso_date()
        row = {
            "filename": fname,
            "extension": ext,
            "filesize_kb": filesize,
            "file_path": folder,
            "date_modified": date_modified,
            "sensitivity": sensitivity
        }
        rows.append(row)
    # enforce rough target distribution
    counts = Counter(r['sensitivity'] for r in rows)
    for cls, target_count in counts_target.items():
        cur = counts.get(cls, 0)
        if cur < target_count:
            need = target_count - cur
            candidates = []
            for idx, r in enumerate(rows):
                key = folder_key(r['file_path'])
                if cls == 'high' and key in ('Customers','Loans','Accounts'):
                    candidates.append(idx)
                elif cls == 'low' and "PublicInfo" in key:
                    candidates.append(idx)
                elif cls == 'medium':
                    candidates.append(idx)
            random.shuffle(candidates)
            for idx in candidates[:need]:
                rows[idx]['sensitivity'] = cls
            counts = Counter(r['sensitivity'] for r in rows)
    num_noisy = int(len(rows) * LABEL_NOISE_FRACTION)
    noisy_indices = random.sample(range(len(rows)), num_noisy)
    label_choices = ['high','medium','low']
    for idx in noisy_indices:
        orig = rows[idx]['sensitivity']
        alt = random.choice([c for c in label_choices if c != orig])
        rows[idx]['sensitivity'] = alt
    return rows

def save_json(rows, path=OUTPUT_JSON):
    with open(path,'w',encoding='utf-8') as fh:
        json.dump(rows, fh, indent=4, ensure_ascii=False)

def save_csv(rows, path=OUTPUT_CSV):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path,'w',newline='',encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

# --------------------------- RUN -------------------------------
if __name__ == "__main__":
    print(f"Generating {NUM_ROWS} rows for Finance/Banking (seed={RANDOM_SEED})...")
    dataset = generate_dataset(NUM_ROWS)
    dist = Counter(r['sensitivity'] for r in dataset)
    print("Sensitivity distribution:")
    for k in ['high','medium','low']:
        print(f"  {k:6s} : {dist.get(k,0):6d} ({100.0*dist.get(k,0)/len(dataset):.2f}%)")
    print("\nSample rows (5):")
    for s in random.sample(dataset,5):
        print(s)
    print(f"\nSaving JSON to {OUTPUT_JSON} and CSV to {OUTPUT_CSV} ...")
    save_json(dataset,OUTPUT_JSON)
    save_csv(dataset,OUTPUT_CSV)
    print("Done.")
