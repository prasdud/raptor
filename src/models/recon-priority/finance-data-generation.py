#!/usr/bin/env python3
"""
finance-data-generation-binary.py
Generate realistic synthetic finance/banking file-metadata for training a sensitive/not-sensitive classifier.
"""

import json, csv, random, datetime
from collections import Counter

# --------------------------- CONFIG ---------------------------
NUM_ROWS = 25000
RANDOM_SEED = 42
OUTPUT_JSON = "master-finance-data-binary.json"
OUTPUT_CSV  = "master-finance-data-binary.csv"

# Binary sensitivity distribution
TARGET_DISTRIBUTION = {
    "sensitive": 0.30,   # ~30% sensitive
    "not_sensitive": 0.70
}

FOLDERS = [
    'C:/Finance/Accounts/',
    'C:/Finance/Customers/',
    'C:/Finance/Loans/',
    'C:/Finance/Transactions/',
    'C:/Finance/HR/',
    'C:/Finance/Reports/',
    'C:/Finance/Compliance/',
    'C:/Finance/PublicInfo/',
    'C:/Finance/Internal/'
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

SENSITIVE_KEYWORDS = [
    "confidential","customer","ssn","account_number","pin","loan_contract",
    "salary","audit","passwords","tax_info","credit_report","bank_statement"
]

DATE_START = datetime.datetime(2022, 1, 1)
DATE_END   = datetime.datetime(2025, 12, 31)

random.seed(RANDOM_SEED)

# ------------------------ UTILITIES ---------------------------
def weighted_choice(choices):
    total = sum(w for _, w in choices)
    r = random.random() * total
    upto = 0
    for item, weight in choices:
        if upto + weight >= r: return item
        upto += weight
    return choices[-1][0]

def folder_key(folder_path):
    parts = [p for p in folder_path.split('/') if p]
    return parts[-1] if parts else 'Unknown'

def pick_extension(folder):
    key = folder_key(folder)
    exts = EXT_BY_FOLDER.get(key, ['.pdf','.txt','.csv','.docx','.xlsx'])
    weights = [(ext, 1.0) for ext in exts]
    return weighted_choice(weights)

def random_iso_date():
    delta = int((DATE_END - DATE_START).total_seconds())
    dt = DATE_START + datetime.timedelta(seconds=random.randint(0, delta))
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def filesize_by_ext_and_sensitivity(ext, sensitive):
    ext = ext.lower()
    if ext=='.txt': base=random.randint(1,150)
    elif ext=='.csv': base=int(random.gauss(300,250))
    elif ext in ('.xls','.xlsx'): base=int(random.gauss(700,800))
    elif ext=='.pdf': base=int(random.gauss(800,900))
    elif ext=='.docx': base=int(random.gauss(400,350))
    else: base=int(random.gauss(400,500))
    factor = 1.15 if sensitive else 0.9
    adj = abs(int(random.gauss(factor, 0.05)*base))
    return max(1, min(adj, 10000))

def choose_sensitive(folder, ext, keywords):
    probs = TARGET_DISTRIBUTION.copy()
    key = folder_key(folder)
    # "Customers", "Loans", "Accounts" more likely sensitive
    if key in ("Customers","Loans","Accounts"):
        probs['sensitive'] += 0.15
        probs['not_sensitive'] -= 0.15
    # Keywords boost
    for kw in keywords:
        if kw in SENSITIVE_KEYWORDS:
            probs['sensitive'] += 0.20
            probs['not_sensitive'] -= 0.20
    # Normalize
    total = sum(probs.values())
    probs = {k: max(v/total,0) for k,v in probs.items()}
    return weighted_choice(list(probs.items()))

def generate_filename(folder, ext, idx):
    key = folder_key(folder)
    tokens = {
        'Accounts':['ledger','balance','account','audit'],
        'Customers':['customer','profile','info','contract'],
        'Loans':['loan','agreement','repayment','contract'],
        'Transactions':['transaction','transfer','statement','summary'],
        'HR':['payroll','salary','roster','report'],
        'Reports':['report','analysis','summary','memo'],
        'Compliance':['policy','guideline','audit','review'],
        'PublicInfo':['announcement','notice','info','schedule'],
        'Internal':['procedure','policy','protocol','guideline']
    }.get(key,[key.lower()])
    base=random.choice(tokens)
    keywords=[]
    if random.random()<0.15: keywords=[random.choice(SENSITIVE_KEYWORDS)]
    filename_body=f"{base}_{idx:04d}"
    if keywords: filename_body=f"{keywords[0]}_{filename_body}"
    return filename_body+ext, keywords

# ------------------------ MAIN GENERATOR -----------------------
def generate_dataset(num_rows=NUM_ROWS):
    rows=[]
    for i in range(num_rows):
        folder=random.choice(FOLDERS)
        ext=pick_extension(folder)
        fname, keywords=generate_filename(folder, ext, i)
        sensitive = choose_sensitive(folder, ext, keywords)
        filesize = filesize_by_ext_and_sensitivity(ext, sensitive=='sensitive')
        date_modified = random_iso_date()
        rows.append({
            "filename": fname,
            "extension": ext,
            "filesize_kb": filesize,
            "file_path": folder,
            "date_modified": date_modified,
            "sensitive": 1 if sensitive=='sensitive' else 0,
            "keywords": keywords
        })
    return rows

def save_json(rows, path=OUTPUT_JSON):
    with open(path,'w',encoding='utf-8') as fh:
        json.dump(rows, fh, indent=4, ensure_ascii=False)

def save_csv(rows, path=OUTPUT_CSV):
    if not rows: return
    keys=list(rows[0].keys())
    with open(path,'w',newline='',encoding='utf-8') as fh:
        writer=csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        for r in rows: writer.writerow(r)

# --------------------------- RUN -------------------------------
if __name__=="__main__":
    print(f"Generating {NUM_ROWS} rows for Finance/Banking (seed={RANDOM_SEED})...")
    dataset = generate_dataset(NUM_ROWS)
    dist = Counter(r['sensitive'] for r in dataset)
    print("Sensitive distribution:")
    print(f"  Sensitive     : {dist.get(1,0)} ({100*dist.get(1,0)/len(dataset):.2f}%)")
    print(f"  Not Sensitive : {dist.get(0,0)} ({100*dist.get(0,0)/len(dataset):.2f}%)")
    print("\nSample rows (5):")
    for s in random.sample(dataset,5): print(s)
    print(f"\nSaving JSON to {OUTPUT_JSON} and CSV to {OUTPUT_CSV} ...")
    save_json(dataset)
    save_csv(dataset)
    print("Done.")
