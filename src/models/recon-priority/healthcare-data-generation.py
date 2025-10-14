#!/usr/bin/env python3
"""
healthcare-data-generation.py
Generate realistic synthetic healthcare file-metadata for training Recon Priority AI.

Features:
- Realistic folder/extension correlations
- Filename keywords correlated with sensitivity
- Size/date distributions conditioned on extension & sensitivity
- Configurable class imbalance and dataset size
- Small percentage of label noise (mislabels) to simulate real data
- Outputs JSON and CSV

Usage:
    python gen_health_json_improved.py
"""

import json
import csv
import random
import datetime
from collections import Counter

# --------------------------- CONFIG ---------------------------
NUM_ROWS = 10000           # number of rows to generate, starts from 0
RANDOM_SEED = 42           # change if you want different dataset
OUTPUT_JSON = "master-health-data.json"
OUTPUT_CSV  = "master-health-data.csv"

# Target sensitivity distribution (these sum to 1.0)
TARGET_DISTRIBUTION = {
    "high": 0.12,    # ~12% high (rare)
    "medium": 0.28,  # ~28% medium
    "low": 0.60      # ~60% low (common)
}

# Simulate human labeling errors by flipping this fraction of labels
LABEL_NOISE_FRACTION = 0.03  # 3% mislabeled

# Most folders used in the domain (from your example). Keep trailing slash.
FOLDERS = [
    'C:/Healthcare/Patients/',
    'C:/Healthcare/LabResults/',
    'C:/Healthcare/Insurance/',
    'C:/Healthcare/StaffSchedules/',
    'C:/Healthcare/Meetings/',
    'C:/Healthcare/Maintenance/',
    'C:/Healthcare/PublicInfo/Menu/',
    'C:/Healthcare/PublicInfo/Parking/',
    'C:/Healthcare/PublicInfo/Notices/',
    'C:/Healthcare/Internal/Protocols/'
]

# Allowed extensions and likely extensions per folder (probability-weighted)
EXT_BY_FOLDER = {
    'Patients':    ['.pdf', '.docx', '.xlsx', '.csv'],
    'LabResults':  ['.xls', '.xlsx', '.csv', '.pdf'],
    'Insurance':   ['.pdf', '.docx', '.csv'],
    'StaffSchedules': ['.xlsx', '.csv', '.pdf'],
    'Meetings':    ['.pdf', '.docx', '.txt'],
    'Maintenance': ['.xlsx', '.pdf', '.txt'],
    'PublicInfo':  ['.pdf', '.txt', '.csv'],
    'Internal':    ['.docx', '.pdf', '.xlsx']
}

# Keywords that raise sensitivity odds when present in filename
HIGH_KEYWORDS = [
    "confidential", "patient", "ssn", "diagnosis", "medical", "prescription",
    "payroll", "credentials", "passwords", "audit", "consent", "insurance_claim"
]
MEDIUM_KEYWORDS = [
    "report", "results", "summary", "invoice", "appointment", "lab", "test"
]
LOW_KEYWORDS = [
    "notice", "menu", "parking", "schedule", "announcement", "public", "maintenance"
]

# Date generation window
DATE_START = datetime.datetime(2023, 1, 1, 0, 0, 0)
DATE_END   = datetime.datetime(2025, 12, 31, 23, 59, 59)

# ------------------------ UTILITIES ---------------------------
random.seed(RANDOM_SEED)

def weighted_choice(choices):
    """choices = list of (item, weight)"""
    total = sum(w for _, w in choices)
    r = random.random() * total
    upto = 0.0
    for item, weight in choices:
        if upto + weight >= r:
            return item
        upto += weight
    return choices[-1][0]

def folder_key(folder_path):
    """Return the folder name token used in EXT_BY_FOLDER keys"""
    # 'C:/Healthcare/PublicInfo/Notices/' -> 'PublicInfo' or 'Notices'?
    # We try to match the more specific listing in EXT_BY_FOLDER keys.
    parts = [p for p in folder_path.split('/') if p]
    # pick last two tokens to check for specific buckets
    for candidate in reversed(parts):
        if candidate in EXT_BY_FOLDER:
            return candidate
    # fallback to second last (e.g., 'Notices' not in EXT_BY_FOLDER -> 'PublicInfo')
    if len(parts) >= 2:
        return parts[-2]
    return parts[-1]

def pick_extension_for_folder(folder):
    key = folder_key(folder)
    prefer = EXT_BY_FOLDER.get(key, ['.pdf', '.txt', '.csv', '.docx', '.xlsx', '.xls'])
    # bias selection: earlier items are slightly more probable
    weights = [(ext, max(1.0, 2.0 - 0.2 * i)) for i, ext in enumerate(prefer)]
    return weighted_choice(weights)

def random_iso_date(start=DATE_START, end=DATE_END):
    """Return random ISO8601 datetime string between start and end"""
    delta = int((end - start).total_seconds())
    sec = random.randint(0, delta)
    dt = start + datetime.timedelta(seconds=sec)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def filesize_by_ext_and_sensitivity(ext, sensitivity):
    """
    Return a realistic filesize_kb based on extension & sensitivity.
    Uses different distributions:
     - small text files: 1KB - 100KB
     - spreadsheets/reports: 50KB - 5000KB
     - pdfs: 20KB - 5000KB
    Sensitive files often slightly larger or within specific ranges, but keep variety.
    """
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

    # Sensitivity adjustment: high files may be larger on average
    if sensitivity == "high":
        adj = abs(int(random.gauss(1.15, 0.05) * base))
    elif sensitivity == "medium":
        adj = abs(int(random.gauss(1.0, 0.08) * base))
    else:
        adj = abs(int(random.gauss(0.85, 0.1) * base))

    # clamp to reasonable range
    adj = max(1, min(adj, 10_000))
    return adj

def choose_sensitivity_for_row(folder, extension, filename_keywords):
    """
    Compute a probability-weighted sensitivity value conditioned on folder,
    extension and keywords. This encodes realistic heuristics.
    """
    # base probabilities from TARGET_DISTRIBUTION
    base = TARGET_DISTRIBUTION.copy()

    # folder influence
    key = folder_key(folder)
    if key in ("Patients", "LabResults", "Insurance"):
        # raise high probability for these folders
        base['high'] += 0.10
        base['low']  -= 0.06
    elif "PublicInfo" in key or key in ("Menu", "Notices", "Parking"):
        base['low'] += 0.12
        base['high'] -= 0.06
    elif key in ("Maintenance", "StaffSchedules"):
        base['low'] += 0.06
        base['medium'] += 0.02

    # extension influence
    if extension in ('.xls', '.xlsx', '.pdf', '.docx'):
        base['high'] += 0.03
        base['low']  -= 0.02
    elif extension in ('.txt',):
        base['low'] += 0.03
        base['high'] -= 0.02

    # filename keyword influence
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

    # normalize and clamp
    for k in base:
        base[k] = max(base[k], 0.0)
    s = sum(base.values())
    if s <= 0:
        base = TARGET_DISTRIBUTION.copy()
        s = sum(base.values())
    probs = {k: v / s for k, v in base.items()}

    # weighted selection
    choices = list(probs.items())
    return weighted_choice(choices)

def generate_filename(folder, extension, idx):
    """
    Generate a filename that contains realistic keywords depending on folder.
    We'll sometimes include a high-sensitivity keyword and sometimes a low one.
    """
    key = folder_key(folder)
    base_tokens = {
        'Patients': ['patient', 'visit', 'record', 'consent', 'diagnosis'],
        'LabResults': ['lab', 'results', 'test', 'analysis', 'specimen'],
        'Insurance': ['claim', 'policy', 'coverage', 'invoice', 'reimbursement'],
        'StaffSchedules': ['roster', 'shift', 'schedule'],
        'Meetings': ['minutes', 'agenda', 'meeting'],
        'Maintenance': ['maintenance', 'workorder', 'log'],
        'PublicInfo': ['notice', 'menu', 'parking', 'info'],
        'Internal': ['protocol', 'guideline', 'procedure']
    }
    tokens = base_tokens.get(key, [key.lower()])
    # Decide if we include a special keyword
    p = random.random()
    keywords = []
    if p < 0.08:
        # include a high keyword (8% chance)
        kw = random.choice(HIGH_KEYWORDS)
        keywords.append(kw)
    elif p < 0.28:
        # medium keyword (20% chance)
        kw = random.choice(MEDIUM_KEYWORDS)
        keywords.append(kw)
    elif p < 0.55:
        # low keyword (27% chance)
        kw = random.choice(LOW_KEYWORDS)
        keywords.append(kw)
    # Always include a base token and an index to make names unique
    base = random.choice(tokens)
    filename_body = f"{base}_{idx:04d}"
    # occasionally add an extra descriptor
    if random.random() < 0.12:
        filename_body += "_" + random.choice(['final', 'v2', 'draft', 'archived', 'confidential'])
    # attach keywords near end sometimes
    if keywords and random.random() < 0.9:
        filename_body = f"{keywords[0]}_{filename_body}"
    return filename_body + extension, keywords

# ------------------------ MAIN GENERATOR -----------------------
def generate_dataset(num_rows=NUM_ROWS):
    rows = []
    # Precompute how many per class to enforce approximate target distribution
    counts_target = {k: int(num_rows * v) for k, v in TARGET_DISTRIBUTION.items()}
    # Ensure sum equals num_rows by adjusting 'low' bucket
    remaining = num_rows - sum(counts_target.values())
    counts_target['low'] += remaining

    # We'll generate rows but allow the heuristic to override; at the end we apply label noise.
    for i in range(num_rows):
        folder = random.choice(FOLDERS)
        ext = pick_extension_for_folder(folder)
        fname, keywords = generate_filename(folder, ext, i)

        # Tentative sensitivity from heuristic conditioned on folder/ext/keywords
        sensitivity = choose_sensitivity_for_row(folder, ext, keywords)

        # If choose_sensitivity_for_row returns a selection among 'high','medium','low'
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

    # Post-processing: enforce rough target distribution by re-labeling a small set
    # Count current distribution
    counts = Counter(r['sensitivity'] for r in rows)
    # If any class is underrepresented relative to target, boost some samples by re-labeling
    for cls, target_count in counts_target.items():
        cur = counts.get(cls, 0)
        if cur < target_count:
            need = target_count - cur
            # pick candidate rows that are easy to convert (e.g., folder matches cls)
            candidates = []
            for idx, r in enumerate(rows):
                # Heuristic: if folder suggests this class, consider it
                key = folder_key(r['file_path'])
                if cls == 'high' and key in ('Patients', 'LabResults', 'Insurance'):
                    candidates.append(idx)
                elif cls == 'low' and ('PublicInfo' in key or key in ('Maintenance', 'StaffSchedules')):
                    candidates.append(idx)
                elif cls == 'medium':
                    candidates.append(idx)
            random.shuffle(candidates)
            for idx in candidates[:need]:
                rows[idx]['sensitivity'] = cls
            # update counts
            counts = Counter(r['sensitivity'] for r in rows)

    # Apply label noise (flip label for a small fraction)
    num_noisy = int(len(rows) * LABEL_NOISE_FRACTION)
    noisy_indices = random.sample(range(len(rows)), num_noisy)
    label_choices = ['high', 'medium', 'low']
    for idx in noisy_indices:
        orig = rows[idx]['sensitivity']
        alt = random.choice([c for c in label_choices if c != orig])
        rows[idx]['sensitivity'] = alt
        # keep other fields the same (simulate mislabel)

    return rows

def save_json(rows, path=OUTPUT_JSON):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(rows, fh, indent=4, ensure_ascii=False)

def save_csv(rows, path=OUTPUT_CSV):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

# --------------------------- RUN -------------------------------
if __name__ == "__main__":
    print(f"Generating {NUM_ROWS} rows (seed={RANDOM_SEED})...")
    dataset = generate_dataset(NUM_ROWS)
    # sanity checks
    dist = Counter(r['sensitivity'] for r in dataset)
    print("Sensitivity distribution (after post-processing & noise):")
    for k in ['high', 'medium', 'low']:
        print(f"  {k:6s} : {dist.get(k,0):6d} ({100.0*dist.get(k,0)/len(dataset):.2f}%)")

    # Sample output preview
    print("\nSample rows (5):")
    for s in random.sample(dataset, 5):
        print(s)

    print(f"\nSaving JSON to {OUTPUT_JSON} and CSV to {OUTPUT_CSV} ...")
    save_json(dataset, OUTPUT_JSON)
    save_csv(dataset, OUTPUT_CSV)
    print("Done.")
