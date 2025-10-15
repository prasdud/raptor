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
# Example input (one or more rows)
# ----------------------------
new_data = pd.DataFrame([
    {
        'count_sensitive_files': 2,
        'has_high_sensitivity': 1,
        'max_file_confidence': 0.93,
        'avg_sensitivity_score': 0.81,
        'num_open_ports': 3,
        'has_web_port': 1,
        'num_high_ports': 2,
        'is_admin': 0,
        'interesting_env_keys': 1,
        'last_action': "SIM_LIST_PROCESSES"
    },
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
    }
])

# ----------------------------
# Encode last_action column
# ----------------------------
new_data['last_action'] = last_action_encoder.transform(new_data['last_action'])

# ----------------------------
# Predict using LightGBM model
# ----------------------------
pred_proba = model.predict(new_data)
pred_encoded = np.argmax(pred_proba, axis=1)

# ----------------------------
# Decode predictions back to readable labels
# ----------------------------
pred_labels = action_label_encoder.inverse_transform(pred_encoded)

# ----------------------------
# Show results
# ----------------------------
for i, label in enumerate(pred_labels):
    print(f"Sample {i+1} → Predicted action: {label}")
