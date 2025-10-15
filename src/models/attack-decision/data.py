import random
import numpy as np
import pandas as pd

# ----------------------------
# Configuration
# ----------------------------
NUM_ROWS = 50000
LABEL_NOISE_PERCENT = 0.05  # fraction of rows with random label
CLASS_BALANCE = True         # oversample rarer classes

ACTIONS = [
    "SIM_NO_OP",
    "SIM_READ_FILE",
    "SIM_LIST_PROCESSES",
    "SIM_SCAN_PORT",
    "SIM_READ_ENV",
    "SIM_COLLECT_TELEMETRY"
]

LAST_ACTIONS = ["SIM_NO_OP","SIM_SCAN_PORT","SIM_READ_FILE","SIM_LIST_PROCESSES",
                "SIM_READ_ENV","SIM_COLLECT_TELEMETRY"]

# ----------------------------
# Helper function to generate one row
# ----------------------------
def generate_row():
    # Open ports
    num_open_ports = np.random.poisson(2)
    open_ports = random.sample(range(20, 5000), k=max(0,num_open_ports))

    # Inject realistic web ports
    if random.random() < 0.3:  # 30% chance to have a web port
        open_ports.append(random.choice([80, 443]))

    has_web_port = 1 if any(port in (80, 443) for port in open_ports) else 0
    num_high_ports = sum(1 for p in open_ports if p >= 1024)

    # Sensitive files
    count_sensitive_files = np.random.binomial(1, 0.2) * (1 + np.random.geometric(0.3)-1)
    if count_sensitive_files > 0:
        max_file_conf = np.random.beta(8,1)
        avg_sens = np.random.beta(6,2)
    else:
        max_file_conf = np.random.beta(1,10)
        avg_sens = max_file_conf

    # Environment flags
    is_admin = np.random.binomial(1,0.1)
    interesting_env = np.random.poisson(0.5)
    last_action = random.choice(LAST_ACTIONS)
    has_high_sens = 1 if max_file_conf>0.9 else 0

    # ----------------------------
    # Labeling rules
    # ----------------------------
    if has_high_sens == 1:
        label='SIM_READ_FILE'
    elif is_admin == 1 and interesting_env >= 1:
        label='SIM_LIST_PROCESSES'
    elif (num_open_ports >= 4) or (has_web_port == 1):
        label='SIM_SCAN_PORT'
    elif interesting_env >= 1:
        label='SIM_READ_ENV'
    else:
        label='SIM_COLLECT_TELEMETRY'

    # Inject label noise
    if random.random() < LABEL_NOISE_PERCENT:
        label = random.choice(ACTIONS)

    return {
        'count_sensitive_files': int(count_sensitive_files),
        'has_high_sensitivity': has_high_sens,
        'max_file_confidence': float(round(max_file_conf,4)),
        'avg_sensitivity_score': float(round(avg_sens,4)),
        'num_open_ports': int(num_open_ports),
        'has_web_port': has_web_port,
        'num_high_ports': num_high_ports,
        'is_admin': is_admin,
        'interesting_env_keys': int(interesting_env),
        'last_action': last_action,
        'action_label': label
    }

# ----------------------------
# Generate dataset
# ----------------------------
dataset = [generate_row() for _ in range(NUM_ROWS)]
df = pd.DataFrame(dataset)

# ----------------------------
# Optional: balance classes but keep total NUM_ROWS
# ----------------------------
if CLASS_BALANCE:
    # compute target per class
    target_per_class = NUM_ROWS // len(ACTIONS)
    df_balanced = pd.concat([
        df[df['action_label']==cls].sample(target_per_class, replace=True)
        for cls in ACTIONS
    ])
    df = df_balanced.sample(frac=1).reset_index(drop=True)  # shuffle

# ----------------------------
# Save dataset
# ----------------------------
df.to_csv("attack_decision_dataset_windows.csv", index=False)
print("Synthetic dataset generated: attack_decision_dataset_windows.csv")
print(df['action_label'].value_counts())
