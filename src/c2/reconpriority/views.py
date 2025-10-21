import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import joblib

# ===========================
# Model Path
# ===========================
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'file_sensitivity_model.pkl')

# ===========================
# Load model once at import
# ===========================
model_package = joblib.load(MODEL_PATH)
model = model_package['model']
feature_names = model_package['feature_names']
label_encoders = model_package['label_encoders']

# ===========================
# Feature extraction helpers
# ===========================
def extract_features(df):
    """Extract features similar to training pipeline"""
    features = pd.DataFrame()
    features['filesize_kb'] = df['size_kb']
    features['extension'] = df['extension']

    # Path-based
    features['department'] = df['path'].apply(lambda x: x.split('/')[1] if len(x.split('/')) > 1 else 'unknown')
    features['subdirectory'] = df['path'].apply(lambda x: x.split('/')[2] if len(x.split('/')) > 2 else 'unknown')
    features['path_depth'] = df['path'].apply(lambda x: len(x.split('/')))

    # Filename pattern
    features['has_confidential'] = df['filename'].str.lower().str.contains('confidential|private|secret|internal', regex=True).astype(int)
    features['has_financial'] = df['filename'].str.lower().str.contains('ledger|account|payment|invoice|salary', regex=True).astype(int)
    features['has_medical'] = df['filename'].str.lower().str.contains('patient|medical|health|lab|diagnosis', regex=True).astype(int)
    features['has_legal'] = df['filename'].str.lower().str.contains('agreement|contract|legal|nda', regex=True).astype(int)
    features['has_personal'] = df['filename'].str.lower().str.contains('personal|ssn|dob|employee', regex=True).astype(int)

    # Doc type
    features['doc_type'] = df['filename'].apply(lambda fn: extract_doc_type(fn))

    # Numbers in filename
    features['has_numbers'] = df['filename'].str.contains(r'\d+', regex=True).astype(int)

    # Date features
    df['last_accessed'] = pd.to_datetime(df['last_accessed'])
    features['year'] = df['last_accessed'].dt.year
    features['month'] = df['last_accessed'].dt.month
    features['day_of_week'] = df['last_accessed'].dt.dayofweek
    features['is_recent'] = (df['last_accessed'] > '2024-01-01').astype(int)

    # Size categories
    features['size_category'] = pd.cut(df['size_kb'], 
                                       bins=[0, 50, 200, 1000, float('inf')],
                                       labels=['small', 'medium', 'large', 'very_large'])

    # Sensitive path
    features['in_sensitive_folder'] = df['path'].str.lower().str.contains(
        'accounts|loans|insurance|personal|confidential|private', regex=True).astype(int)

    return features

def extract_doc_type(filename):
    filename_lower = filename.lower()
    doc_types = ['report', 'ledger', 'agreement', 'policy', 'guideline', 
                 'notice', 'memo', 'invoice', 'statement', 'record']
    for dt in doc_types:
        if dt in filename_lower:
            return dt
    return 'other'

def preprocess_features(features):
    categorical_cols = ['extension', 'department', 'subdirectory', 'doc_type', 'size_category']
    for col in categorical_cols:
        features[col] = features[col].astype(str)
        if col in label_encoders:
            le = label_encoders[col]
            # Handle unseen categories
            features[col] = features[col].apply(lambda x: x if x in le.classes_ else 'unknown')
            if 'unknown' not in le.classes_:
                le.classes_ = np.append(le.classes_, 'unknown')
            features[col] = le.transform(features[col])
    return features

# ===========================
# Django view
# ===========================
@csrf_exempt
def predict_file_sensitivity(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)

    try:
        input_data = json.loads(request.body)
        if not isinstance(input_data, list):
            return JsonResponse({"error": "Input must be a list of files"}, status=400)

        # Convert to DataFrame
        df_input = pd.DataFrame(input_data)
        features = extract_features(df_input)
        features = preprocess_features(features)
        features = features[feature_names]  # ensure correct order

        # Predict
        predictions = model.predict(features)
        probabilities = model.predict_proba(features)[:, 1]  # confidence for class 1

        # Build response
        results = []
        for i, row in df_input.iterrows():
            pred_label = "High" if predictions[i] == 1 else "Low"
            results.append({
                "filename": row['filename'],
                "sensitivity": pred_label,
                "sensitivity_binary": int(predictions[i]),
                "path": row['path'],
                "confidence": float(probabilities[i])
            })

        # Summary stats
        count_sensitive_files = int(sum(predictions))
        max_confidence = float(np.max(probabilities)) if len(probabilities) > 0 else None
        avg_confidence = float(np.mean(probabilities)) if len(probabilities) > 0 else None
        has_high_sensitivity = 1 if max_confidence is not None and max_confidence > 0.9 else 0

        response = {
            "files": results,
            "summary": {
                "count_sensitive_files": count_sensitive_files,
                "has_high_sensitivity": has_high_sensitivity,
                "max_file_confidence": max_confidence,
                "avg_sensitivity_score": avg_confidence,
                "num_open_ports": None,
                "has_web_port": None,
                "num_high_ports": None,
                "is_admin": None,
                "interesting_env_keys": None,
                "last_action": None
            }
        }

        return JsonResponse(response, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
