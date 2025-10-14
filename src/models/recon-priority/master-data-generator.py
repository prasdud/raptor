#!/usr/bin/env python3
"""
combine_datasets.py
Combine healthcare and finance datasets into a single master dataset for training/testing.
"""

import json
import csv
import random

# ---------------- CONFIG ----------------
HEALTH_JSON  = "master-health-data-binary.json"
FINANCE_JSON = "master-finance-data-binary.json"
MASTER_JSON  = "master-data.json"
MASTER_CSV   = "master-data.csv"
RANDOM_SEED  = 42

# ---------------- UTILITIES ----------------
def load_json(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=4, ensure_ascii=False)

def save_csv(data, path):
    if not data:
        return
    keys = list(data[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    random.seed(RANDOM_SEED)

    # Load datasets
    health_data  = load_json(HEALTH_JSON)
    finance_data = load_json(FINANCE_JSON)

    print(f"Loaded {len(health_data)} healthcare rows and {len(finance_data)} finance rows")

    # Combine
    master_data = health_data + finance_data
    print(f"Combined dataset: {len(master_data)} rows")

    # Shuffle
    random.shuffle(master_data)

    # Save combined
    save_json(master_data, MASTER_JSON)
    save_csv(master_data, MASTER_CSV)

    print(f"Saved combined dataset to {MASTER_JSON} and {MASTER_CSV}")
