
"""
Complete ML Pipeline for File Sensitivity Classification
Predicts whether files contain sensitive data based on metadata
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, accuracy_score, roc_curve, auc, precision_recall_curve, average_precision_score
from sklearn.preprocessing import LabelEncoder
import lightgbm as lgb
# import joblib
import json
import re
from datetime import datetime
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
warnings.filterwarnings('ignore')


import os
CSV_PATH = 'improved_dataset.csv'
if not os.path.isfile(CSV_PATH):
    print(f"❌ ERROR: CSV file '{CSV_PATH}' not found. Please check the path and try again.")
    exit(1)
df_main = pd.read_csv(CSV_PATH)

class FileSensitivityClassifier:
    """End-to-end pipeline for file sensitivity classification"""
    
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.label_encoders = {}
        
    def extract_features(self, df):
        """Extract meaningful features from raw file metadata"""
        features = pd.DataFrame()
        
        # 1. Basic features
        features['filesize_kb'] = df['filesize_kb']
        features['extension'] = df['extension']
        
        # 2. Path-based features
        features['department'] = df['file_path'].apply(lambda x: x.split('/')[1] if len(x.split('/')) > 1 else 'unknown')
        features['subdirectory'] = df['file_path'].apply(lambda x: x.split('/')[2] if len(x.split('/')) > 2 else 'unknown')
        features['path_depth'] = df['file_path'].apply(lambda x: len(x.split('/')))
        
        # 3. Filename pattern features
        features['has_confidential'] = df['filename'].str.lower().str.contains('confidential|private|secret|internal', regex=True).astype(int)
        features['has_financial'] = df['filename'].str.lower().str.contains('ledger|account|payment|invoice|salary', regex=True).astype(int)
        features['has_medical'] = df['filename'].str.lower().str.contains('patient|medical|health|lab|diagnosis', regex=True).astype(int)
        features['has_legal'] = df['filename'].str.lower().str.contains('agreement|contract|legal|nda', regex=True).astype(int)
        features['has_personal'] = df['filename'].str.lower().str.contains('personal|ssn|dob|employee', regex=True).astype(int)
        
        # Document type from filename
        features['doc_type'] = df['filename'].apply(self._extract_doc_type)
        
        # Has numbers in filename (often IDs)
        features['has_numbers'] = df['filename'].str.contains(r'\d+', regex=True).astype(int)
        
        # 4. Date features
        df['date_modified'] = pd.to_datetime(df['date_modified'])
        features['year'] = df['date_modified'].dt.year
        features['month'] = df['date_modified'].dt.month
        features['day_of_week'] = df['date_modified'].dt.dayofweek
        features['is_recent'] = (df['date_modified'] > '2024-01-01').astype(int)
        
        # 5. File size categories
        features['size_category'] = pd.cut(df['filesize_kb'], 
                                           bins=[0, 50, 200, 1000, float('inf')],
                                           labels=['small', 'medium', 'large', 'very_large'])
        
        # 6. Sensitive path indicators
        features['in_sensitive_folder'] = df['file_path'].str.lower().str.contains(
            'accounts|loans|insurance|personal|confidential|private', regex=True).astype(int)
        
        return features
    
    def _extract_doc_type(self, filename):
        """Extract document type from filename"""
        filename_lower = filename.lower()
        doc_types = ['report', 'ledger', 'agreement', 'policy', 'guideline', 
                     'notice', 'memo', 'invoice', 'statement', 'record']
        for doc_type in doc_types:
            if doc_type in filename_lower:
                return doc_type
        return 'other'
    
    def preprocess_features(self, features, is_training=True):
        """Encode categorical features"""
        categorical_cols = ['extension', 'department', 'subdirectory', 'doc_type', 'size_category']
        
        for col in categorical_cols:
            if is_training:
                self.label_encoders[col] = LabelEncoder()
                features[col] = self.label_encoders[col].fit_transform(features[col].astype(str))
            else:
                # Handle unseen categories during inference
                features[col] = features[col].astype(str)
                features[col] = features[col].apply(
                    lambda x: x if x in self.label_encoders[col].classes_ else 'unknown'
                )
                # Add 'unknown' to encoder if not present
                if 'unknown' not in self.label_encoders[col].classes_:
                    self.label_encoders[col].classes_ = np.append(self.label_encoders[col].classes_, 'unknown')
                features[col] = self.label_encoders[col].transform(features[col])
        
        return features
    
    def train(self, df):
        """Train the model on your dataset (df is a DataFrame)"""
        print(f"📁 Using loaded dataset with {len(df)} records")

        # Extract features
        print("\n🔧 Engineering features...")
        features = self.extract_features(df)
        features = self.preprocess_features(features, is_training=True)
        self.feature_names = features.columns.tolist()

        # Target variable
        y = df['sensitive']

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"✓ Training set: {len(X_train)} | Test set: {len(X_test)}")
        print(f"✓ Class distribution: {y.value_counts().to_dict()}")

        # Train LightGBM model with improved hyperparameters
        print("\n🚀 Training LightGBM model...")
        self.model = lgb.LGBMClassifier(
            n_estimators=500,  # Increased from 200
            learning_rate=0.03,  # Lower for better generalization
            max_depth=8,  # Slightly deeper
            num_leaves=50,  # More leaves for complex patterns
            min_child_samples=15,  # Reduced for better sensitivity
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.1,  # L1 regularization
            reg_lambda=0.1,  # L2 regularization
            random_state=42,
            verbose=-1,
            class_weight='balanced',  # Handle imbalanced data
            scale_pos_weight=1.8  # Extra weight for sensitive class
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        print("\n📊 Evaluating model...")
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]

        print(f"\n✓ Accuracy: {accuracy_score(y_test, y_pred):.4f}")
        print(f"✓ ROC-AUC: {roc_auc_score(y_test, y_pred_proba):.4f}")

        # Classification report
        from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc, precision_recall_curve, average_precision_score
        report = classification_report(y_test, y_pred, target_names=['Not Sensitive', 'Sensitive'], output_dict=True)
        print("\n📈 Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Not Sensitive', 'Sensitive']))

        # Confusion Matrix
        print("\n🎯 Confusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(f"True Negatives: {cm[0,0]} | False Positives: {cm[0,1]}")
        print(f"False Negatives: {cm[1,0]} | True Positives: {cm[1,1]}")
        import matplotlib.pyplot as plt
        import seaborn as sns
        plt.figure(figsize=(6,4))
        sns.heatmap(cm, annot=True, fmt='d', xticklabels=['Not Sensitive', 'Sensitive'], yticklabels=['Not Sensitive', 'Sensitive'], cmap='Blues')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title('Confusion Matrix')
        plt.tight_layout()
        plt.savefig("confusion_matrix.png")
        plt.close()

        # Feature importance
        print("\n🔍 Top 10 Most Important Features:")
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False).head(10)
        print(feature_importance.to_string(index=False))
        plt.figure(figsize=(8,5))
        sns.barplot(x='importance', y='feature', data=feature_importance)
        plt.title('Top 10 Feature Importances')
        plt.tight_layout()
        plt.savefig("feature_importance.png")
        plt.close()

        # ROC Curve
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        roc_auc = auc(fpr, tpr)
        plt.figure(figsize=(6,5))
        plt.plot(fpr, tpr, color='blue', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
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

        # Precision-Recall Curve
        precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
        avg_precision = average_precision_score(y_test, y_pred_proba)
        plt.figure(figsize=(6,5))
        plt.plot(recall, precision, color='green', lw=2, label=f'PR curve (AP = {avg_precision:.2f})')
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curve')
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig("precision_recall_curve.png")
        plt.close()

        # Per-class Precision, Recall, F1-score Bar Plots
        metrics = ['precision', 'recall', 'f1-score']
        for metric in metrics:
            values = [report[cls][metric] for cls in ['Not Sensitive', 'Sensitive']]
            plt.figure(figsize=(6,4))
            sns.barplot(x=['Not Sensitive', 'Sensitive'], y=values)
            plt.ylim(0,1)
            plt.title(f'Per-class {metric.capitalize()}')
            plt.ylabel(metric.capitalize())
            plt.xlabel('Class')
            plt.tight_layout()
            plt.savefig(f"per_class_{metric}.png")
            plt.close()

        # Classification Report Table as Image
        report_df = pd.DataFrame(report).transpose()
        plt.figure(figsize=(6,2))
        sns.heatmap(report_df.iloc[:2, :-1], annot=True, cmap='YlGnBu', fmt='.2f')
        plt.title('Classification Report')
        plt.tight_layout()
        plt.savefig("classification_report.png")
        plt.close()

        # Learning Curve (if available)
        if hasattr(self.model, 'evals_result_'):
            evals_result = self.model.evals_result_
            if 'training' in evals_result and 'valid_1' in evals_result:
                plt.figure(figsize=(8,5))
                plt.plot(evals_result['training']['binary_logloss'], label='Train Logloss')
                plt.plot(evals_result['valid_1']['binary_logloss'], label='Test Logloss')
                plt.xlabel('Iteration')
                plt.ylabel('Logloss')
                plt.title('Learning Curve (Logloss)')
                plt.legend()
                plt.tight_layout()
                plt.savefig("learning_curve.png")
                plt.close()

        # Cross-validation
        print("\n🔄 Cross-validation scores (5-fold):")
        cv_scores = cross_val_score(self.model, features, y, cv=5, scoring='roc_auc')
        print(f"Mean ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

        return self
    
    def save_model(self, model_path='file_sensitivity_model.pkl'):
        """Save trained model and encoders"""
        model_package = {
            'model': self.model,
            'feature_names': self.feature_names,
            'label_encoders': self.label_encoders
        }
        joblib.dump(model_package, model_path)
        print(f"\n💾 Model saved to: {model_path}")
    
    def load_model(self, model_path='file_sensitivity_model.pkl'):
        """Load trained model"""
        model_package = joblib.load(model_path)
        self.model = model_package['model']
        self.feature_names = model_package['feature_names']
        self.label_encoders = model_package['label_encoders']
        print(f"✓ Model loaded from: {model_path}")
        return self
    
    def predict(self, input_json):
        """
        Predict sensitivity for a single file
        
        Input JSON format:
        {
            "filename": "confidential_report.pdf",
            "extension": ".pdf",
            "size_kb": 2048,
            "path": "C:/Users/Admin/Documents/",
            "last_accessed": "2025-08-14"
        }
        
        Output JSON format:
        {
            "filename": "confidential_report.pdf",
            "sensitivity": "High",  # or 1 for sensitive, 0 for not sensitive
            "path": "C:/Users/Admin/Documents/",
            "confidence": 0.95
        }
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded. Call train() or load_model() first.")
        
        # Parse input
        if isinstance(input_json, str):
            input_data = json.loads(input_json)
        else:
            input_data = input_json
        
        # Convert to DataFrame format expected by extract_features
        df_input = pd.DataFrame([{
            'filename': input_data['filename'],
            'extension': input_data['extension'],
            'filesize_kb': input_data['size_kb'],
            'file_path': input_data['path'],
            'date_modified': input_data.get('last_accessed', datetime.now().strftime('%Y-%m-%d')),
            'keywords': []
        }])
        
        # Extract and preprocess features
        features = self.extract_features(df_input)
        features = self.preprocess_features(features, is_training=False)
        
        # Ensure feature order matches training
        features = features[self.feature_names]
        
        # Predict
        prediction = self.model.predict(features)[0]
        probability = self.model.predict_proba(features)[0]
        confidence = probability[prediction]
        
        # Format output
        sensitivity_label = "High" if prediction == 1 else "Low"
        
        output = {
            "filename": input_data['filename'],
            "sensitivity": sensitivity_label,  # "High" or "Low"
            "sensitivity_binary": int(prediction),  # 1 or 0
            "path": input_data['path'],
            "confidence": float(confidence)
        }
        
        return output


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def main():
    """Example usage of the complete pipeline"""
    
    # Initialize classifier
    classifier = FileSensitivityClassifier()
    
    # STEP 1: Train the model on your CSV
    print("="*70)
    print("STEP 1: TRAINING MODEL")
    print("="*70)
    classifier.train(df_main)
    
    # STEP 2: Save the model (disabled)
    # print("\n" + "="*70)
    # print("STEP 2: SAVING MODEL")
    # print("="*70)
    # classifier.save_model('file_sensitivity_model.pkl')
    
    # STEP 3: Test inference with example inputs
    print("\n" + "="*70)
    print("STEP 3: TESTING PREDICTIONS")
    print("="*70)
    
    # Example 1: Potentially sensitive file
    test_input_1 = {
        "filename": "confidential_report.pdf",
        "extension": ".pdf",
        "size_kb": 2048,
        "path": "C:/Finance/Accounts/",
        "last_accessed": "2025-08-14"
    }
    
    print("\n📄 Test Input 1:")
    print(json.dumps(test_input_1, indent=2))
    
    result_1 = classifier.predict(test_input_1)
    print("\n✅ Prediction Output:")
    print(json.dumps(result_1, indent=2))
    
    # Example 2: Likely non-sensitive file
    test_input_2 = {
        "filename": "public_notice_123.pdf",
        "extension": ".pdf",
        "size_kb": 150,
        "path": "C:/Finance/PublicInfo/",
        "last_accessed": "2024-03-10"
    }
    
    print("\n" + "-"*70)
    print("\n📄 Test Input 2:")
    print(json.dumps(test_input_2, indent=2))
    
    result_2 = classifier.predict(test_input_2)
    print("\n✅ Prediction Output:")
    print(json.dumps(result_2, indent=2))
    
    # Example 3: Medical file
    test_input_3 = {
        "filename": "patient_lab_results_9926.csv",
        "extension": ".csv",
        "size_kb": 45,
        "path": "C:/Healthcare/LabResults/",
        "last_accessed": "2024-11-20"
    }
    
    print("\n" + "-"*70)
    print("\n📄 Test Input 3:")
    print(json.dumps(test_input_3, indent=2))
    
    result_3 = classifier.predict(test_input_3)
    print("\n✅ Prediction Output:")
    print(json.dumps(result_3, indent=2))


def load_and_predict_example():
    """Example: Loading a saved model and making predictions"""
    print("\n" + "="*70)
    print("LOADING SAVED MODEL FOR INFERENCE")
    print("="*70)
    
    # Load pre-trained model
    classifier = FileSensitivityClassifier()
    classifier.load_model('file_sensitivity_model.pkl')
    
    # Make prediction
    new_file = {
        "filename": "employee_salary_ledger.xlsx",
        "extension": ".xlsx",
        "size_kb": 890,
        "path": "C:/Finance/Internal/",
        "last_accessed": "2025-01-15"
    }
    
    result = classifier.predict(new_file)
    print("\n🎯 Prediction for new file:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    # Run the complete pipeline
    main()
    
    # Uncomment below to test loading a saved model
    # load_and_predict_example()