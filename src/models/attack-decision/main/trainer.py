
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
# import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, roc_auc_score, precision_recall_curve, average_precision_score
from sklearn.preprocessing import label_binarize
import matplotlib.ticker as mticker
import itertools

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
# Evaluation & Visualizations
# ----------------------------
acc = accuracy_score(y_test, y_pred)
print(f"Overall Accuracy: {acc:.4f}")

print("\nClassification Report:")
report = classification_report(y_test, y_pred, target_names=le_label.classes_, output_dict=True)
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

# 1. ROC Curve (One-vs-Rest)
Y_test_bin = label_binarize(y_test, classes=range(len(ACTIONS)))
y_pred_proba = np.array(y_pred_proba)
fpr = dict()
tpr = dict()
roc_auc = dict()
for i in range(len(ACTIONS)):
    fpr[i], tpr[i], _ = roc_curve(Y_test_bin[:, i], y_pred_proba[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])
plt.figure(figsize=(8,6))
colors = itertools.cycle(['aqua', 'darkorange', 'cornflowerblue', 'green', 'red', 'purple'])
for i, color in zip(range(len(ACTIONS)), colors):
    plt.plot(fpr[i], tpr[i], color=color, lw=2,
             label=f'ROC curve of class {ACTIONS[i]} (area = {roc_auc[i]:0.2f})')
plt.plot([0, 1], [0, 1], 'k--', lw=2)
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic (ROC) Curve')
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig("roc_curve.png")
plt.close()

# 2. Precision-Recall Curve (One-vs-Rest)
precision = dict()
recall = dict()
avg_precision = dict()
for i in range(len(ACTIONS)):
    precision[i], recall[i], _ = precision_recall_curve(Y_test_bin[:, i], y_pred_proba[:, i])
    avg_precision[i] = average_precision_score(Y_test_bin[:, i], y_pred_proba[:, i])
plt.figure(figsize=(8,6))
for i, color in zip(range(len(ACTIONS)), colors):
    plt.plot(recall[i], precision[i], color=color, lw=2,
             label=f'PR curve of class {ACTIONS[i]} (AP = {avg_precision[i]:0.2f})')
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('Precision-Recall Curve')
plt.legend(loc="best")
plt.tight_layout()
plt.savefig("precision_recall_curve.png")
plt.close()

# 3. Per-class Precision, Recall, F1-score Bar Plots
metrics = ['precision', 'recall', 'f1-score']
for metric in metrics:
    values = [report[str(cls)][metric] for cls in le_label.classes_]
    plt.figure(figsize=(8,5))
    sns.barplot(x=le_label.classes_, y=values)
    plt.ylim(0,1)
    plt.title(f'Per-class {metric.capitalize()}')
    plt.ylabel(metric.capitalize())
    plt.xlabel('Class')
    plt.tight_layout()
    plt.savefig(f"per_class_{metric}.png")
    plt.close()

# 4. Classification Report Table as Image
report_df = pd.DataFrame(report).transpose()
plt.figure(figsize=(8,4))
sns.heatmap(report_df.iloc[:-3, :-1], annot=True, cmap='YlGnBu', fmt='.2f')
plt.title('Classification Report')
plt.tight_layout()
plt.savefig("classification_report.png")
plt.close()

# 5. Learning Curve (Optional: train/test loss vs. iteration)
if hasattr(lgb_model, 'evals_result'):
    evals_result = lgb_model.evals_result()
    if 'train' in evals_result and 'test' in evals_result:
        plt.figure(figsize=(8,5))
        plt.plot(evals_result['train']['multi_logloss'], label='Train Logloss')
        plt.plot(evals_result['test']['multi_logloss'], label='Test Logloss')
        plt.xlabel('Iteration')
        plt.ylabel('Logloss')
        plt.title('Learning Curve (Logloss)')
        plt.legend()
        plt.tight_layout()
        plt.savefig("learning_curve.png")
        plt.close()

# ----------------------------
# Example Inference
# ----------------------------
example_input = X_test.iloc[0:1]
pred_proba = lgb_model.predict(example_input)
pred_label = le_label.inverse_transform([np.argmax(pred_proba)])
confidence = np.max(pred_proba)
print(f"Example Predicted Action: {pred_label[0]}, Confidence: {confidence:.4f}")

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
# joblib.dump(lgb_model, "attack_decision_lgbm_model.pkl")
# joblib.dump(le_label, "action_label_encoder.pkl")
# joblib.dump(le_last_action, "last_action_encoder.pkl")
# print("Model and encoders saved for later use.")

# ----------------------------
# Example Inference
# ----------------------------
example_input = X_test.iloc[0:1]
pred_proba = lgb_model.predict(example_input)
pred_label = le_label.inverse_transform([np.argmax(pred_proba)])
confidence = np.max(pred_proba)
print(f"Example Predicted Action: {pred_label[0]}, Confidence: {confidence:.4f}")
