import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# ----------------------------
# Load Dataset
# ----------------------------
df = pd.read_csv("../attack_decision_dataset_windows.csv")
print("Dataset loaded, shape:", df.shape)

# ----------------------------
# Preprocessing
# ----------------------------
# Encode categorical 'last_action' as numeric
le_last_action = LabelEncoder()
df['last_action_encoded'] = le_last_action.fit_transform(df['last_action'])

# Features and label
feature_cols = [
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
X = df[feature_cols]
y = df['action_label']

# Encode target labels
le_label = LabelEncoder()
y_encoded = le_label.fit_transform(y)

# Define ACTIONS as unique action labels
ACTIONS = le_label.classes_

# ----------------------------
# Train/Test Split
# ----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

# ----------------------------
# LightGBM Dataset
# ----------------------------
train_data = lgb.Dataset(X_train, label=y_train)
test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

# ----------------------------
# LightGBM Parameters
# ----------------------------
params = {
    'objective': 'multiclass',
    'num_class': len(ACTIONS),
    'boosting_type': 'gbdt',
    'metric': 'multi_logloss',
    'learning_rate': 0.1,
    'num_leaves': 31,
    'max_depth': 6,
    'seed': 42
}

# ----------------------------
# Train Model
# ----------------------------
num_round = 200
lgb_model = lgb.train(
    params,
    train_data,
    num_round,
    valid_sets=[train_data, test_data],
    valid_names=['train','test'],
    callbacks=[
        lgb.early_stopping(stopping_rounds=20),
        lgb.log_evaluation(period=20)
    ]
)

# ----------------------------
# Predictions
# ----------------------------
y_pred_proba = lgb_model.predict(X_test)
y_pred = np.argmax(y_pred_proba, axis=1)

# ----------------------------
# Evaluation
# ----------------------------
acc = accuracy_score(y_test, y_pred)
print(f"Overall Accuracy: {acc:.4f}")

print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=le_label.classes_))

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
print("\nConfusion Matrix (rows=Actual, cols=Predicted):")
print(cm)
plt.figure(figsize=(8,6))
sns.heatmap(cm, annot=True, fmt='d', xticklabels=le_label.classes_, yticklabels=le_label.classes_, cmap='Blues')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.tight_layout()
plt.savefig("confusion_matrix.png")
plt.close()

# Feature Importance
importance = lgb_model.feature_importance()
feature_names = X_train.columns
print("\nFeature Importances:")
for name, score in zip(feature_names, importance):
    print(f"{name}: {score}")
plt.figure(figsize=(10,6))
sns.barplot(x=importance, y=feature_names)
plt.title('Feature Importance')
plt.tight_layout()
plt.savefig("feature_importance.png")
plt.close()

# ----------------------------
# Save Model and Encoders
# ----------------------------
joblib.dump(lgb_model, "attack_decision_lgbm_model.pkl")
joblib.dump(le_label, "action_label_encoder.pkl")
joblib.dump(le_last_action, "last_action_encoder.pkl")
print("Model and encoders saved for later use.")

# ----------------------------
# Example Inference
# ----------------------------
example_input = X_test.iloc[0:1]
pred_proba = lgb_model.predict(example_input)
pred_label = le_label.inverse_transform([np.argmax(pred_proba)])
confidence = np.max(pred_proba)
print(f"Example Predicted Action: {pred_label[0]}, Confidence: {confidence:.4f}")
