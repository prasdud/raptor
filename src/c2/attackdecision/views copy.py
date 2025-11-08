import os
import joblib
import numpy as np
import pandas as pd
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status

# Load the trained model and encoders once
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "attack_decision_lgbm_model.pkl")
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, "action_label_encoder.pkl")
LAST_ACTION_ENCODER_PATH = os.path.join(BASE_DIR, "last_action_encoder.pkl")

lgb_model = joblib.load(MODEL_PATH)
action_label_encoder = joblib.load(LABEL_ENCODER_PATH)
last_action_encoder = joblib.load(LAST_ACTION_ENCODER_PATH)

# Feature order (must match training order)
FEATURE_COLUMNS = [
    'count_sensitive_files',
    'has_high_sensitivity',
    'max_file_confidence',
    'avg_sensitivity_score',
    'num_open_ports',
    'has_web_port',
    'num_high_ports',
    'is_admin',
    'interesting_env_keys',
    'last_action_encoded'
]

@api_view(['POST'])
def attack_decision(request):
    """
    Predict the next simulated attacker action based on system recon data.
    """
    try:
        data = request.data

        # Validate required fields
        required_fields = [
            'count_sensitive_files', 'has_high_sensitivity', 'max_file_confidence',
            'avg_sensitivity_score', 'num_open_ports', 'has_web_port', 'num_high_ports',
            'is_admin', 'interesting_env_keys', 'last_action'
        ]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return JsonResponse(
                {"error": f"Missing fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Encode last_action
        last_action_str = data['last_action']
        if last_action_str not in last_action_encoder.classes_:
            return JsonResponse(
                {"error": f"Unknown last_action '{last_action_str}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        last_action_encoded = last_action_encoder.transform([last_action_str])[0]

        # Build feature vector
        features = [
            data['count_sensitive_files'],
            data['has_high_sensitivity'],
            data['max_file_confidence'],
            data['avg_sensitivity_score'],
            data['num_open_ports'],
            data['has_web_port'],
            data['num_high_ports'],
            data['is_admin'],
            data['interesting_env_keys'],
            last_action_encoded
        ]

        X_input = pd.DataFrame([features], columns=FEATURE_COLUMNS)

        # Predict
        y_pred_proba = lgb_model.predict(X_input)
        y_pred = np.argmax(y_pred_proba, axis=1)[0]
        predicted_action = action_label_encoder.inverse_transform([y_pred])[0]
        confidence = float(np.max(y_pred_proba))

        return JsonResponse({
            "predicted_action": predicted_action,
            "confidence": confidence
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
