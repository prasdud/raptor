import joblib
import pandas as pd
import numpy as np

# ----------------------------
# Load model and encoders
# ----------------------------
model = joblib.load("attack_decision_lgbm_model.pkl")
last_action_encoder = joblib.load("last_action_encoder.pkl")
action_label_encoder = joblib.load("action_label_encoder.pkl")

# ----------------------------
# Example input (multiple diverse samples)
# ----------------------------
new_data = pd.DataFrame([
    # High sensitivity → SIM_READ_FILE
    {
        'count_sensitive_files': 3,
        'has_high_sensitivity': 1,
        'max_file_confidence': 0.95,
        'avg_sensitivity_score': 0.88,
        'num_open_ports': 2,
        'has_web_port': 0,
        'num_high_ports': 1,
        'is_admin': 0,
        'interesting_env_keys': 0,
        'last_action': "SIM_LIST_PROCESSES"
    },
    # Admin + interesting env → SIM_LIST_PROCESSES
    {
        'count_sensitive_files': 1,
        'has_high_sensitivity': 0,
        'max_file_confidence': 0.2,
        'avg_sensitivity_score': 0.18,
        'num_open_ports': 2,
        'has_web_port': 0,
        'num_high_ports': 1,
        'is_admin': 1,
        'interesting_env_keys': 2,
        'last_action': "SIM_SCAN_PORT"
    },
    # Many open ports or web port → SIM_SCAN_PORT
    {
        'count_sensitive_files': 0,
        'has_high_sensitivity': 0,
        'max_file_confidence': 0.1,
        'avg_sensitivity_score': 0.08,
        'num_open_ports': 6,
        'has_web_port': 1,
        'num_high_ports': 5,
        'is_admin': 0,
        'interesting_env_keys': 0,
        'last_action': "SIM_READ_ENV"
    },
    # Has interesting environment → SIM_READ_ENV
    {
        'count_sensitive_files': 0,
        'has_high_sensitivity': 0,
        'max_file_confidence': 0.1,
        'avg_sensitivity_score': 0.1,
        'num_open_ports': 1,
        'has_web_port': 0,
        'num_high_ports': 1,
        'is_admin': 0,
        'interesting_env_keys': 3,
        'last_action': "SIM_NO_OP"
    },
    # Nothing special → SIM_COLLECT_TELEMETRY
    {
        'count_sensitive_files': 0,
        'has_high_sensitivity': 0,
        'max_file_confidence': 0.05,
        'avg_sensitivity_score': 0.07,
        'num_open_ports': 1,
        'has_web_port': 0,
        'num_high_ports': 1,
        'is_admin': 0,
        'interesting_env_keys': 0,
        'last_action': "SIM_NO_OP"
    },
    # Random mixed case
    {
        'count_sensitive_files': 2,
        'has_high_sensitivity': 0,
        'max_file_confidence': 0.45,
        'avg_sensitivity_score': 0.42,
        'num_open_ports': 3,
        'has_web_port': 1,
        'num_high_ports': 2,
        'is_admin': 1,
        'interesting_env_keys': 1,
        'last_action': "SIM_SCAN_PORT"
    }
])

# ----------------------------
# Encode last_action
# ----------------------------
new_data['last_action'] = last_action_encoder.transform(new_data['last_action'])

# ----------------------------
# Predict
# ----------------------------
pred_proba = model.predict(new_data)
pred_encoded = np.argmax(pred_proba, axis=1)
pred_labels = action_label_encoder.inverse_transform(pred_encoded)

# ----------------------------
# Display results
# ----------------------------
for i, label in enumerate(pred_labels):
    print(f"Sample {i+1} → Predicted action: {label}")
