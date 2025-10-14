======================================================================
STEP 1: TRAINING MODEL
======================================================================
📁 Loading dataset...
✓ Loaded 50000 records

🔧 Engineering features...
✓ Training set: 40000 | Test set: 10000
✓ Class distribution: {1: 28687, 0: 21313}

🚀 Training LightGBM model...

📊 Evaluating model...

✓ Accuracy: 0.8526
✓ ROC-AUC: 0.9254

📈 Classification Report:
               precision    recall  f1-score   support

Not Sensitive       0.78      0.91      0.84      4263
    Sensitive       0.93      0.81      0.86      5737

     accuracy                           0.85     10000
    macro avg       0.85      0.86      0.85     10000
 weighted avg       0.86      0.85      0.85     10000


🎯 Confusion Matrix:
True Negatives: 3900 | False Positives: 363
False Negatives: 1111 | True Positives: 4626

🔍 Top 10 Most Important Features:
      feature  importance
  filesize_kb        6330
        month        3076
 subdirectory        2868
  day_of_week        2163
    extension        1566
         year        1434
     doc_type         982
    has_legal         395
 has_personal         357
size_category         343

🔄 Cross-validation scores (5-fold):
Mean ROC-AUC: 0.9249 (+/- 0.0044)

======================================================================
STEP 2: SAVING MODEL
======================================================================

💾 Model saved to: file_sensitivity_model.pkl

======================================================================
STEP 3: TESTING PREDICTIONS
======================================================================

📄 Test Input 1:
{
  "filename": "confidential_report.pdf",
  "extension": ".pdf",
  "size_kb": 2048,
  "path": "C:/Finance/Accounts/",
  "last_accessed": "2025-08-14"
}

✅ Prediction Output:
{
  "filename": "confidential_report.pdf",
  "sensitivity": "High",
  "sensitivity_binary": 1,
  "path": "C:/Finance/Accounts/",
  "confidence": 0.9999325184226912
}

----------------------------------------------------------------------

📄 Test Input 2:
{
  "filename": "public_notice_123.pdf",
  "extension": ".pdf",
  "size_kb": 150,
  "path": "C:/Finance/PublicInfo/",
  "last_accessed": "2024-03-10"
}

✅ Prediction Output:
{
  "filename": "public_notice_123.pdf",
  "sensitivity": "Low",
  "sensitivity_binary": 0,
  "path": "C:/Finance/PublicInfo/",
  "confidence": 0.9981951394561533
}

----------------------------------------------------------------------

📄 Test Input 3:
{
  "filename": "patient_lab_results_9926.csv",
  "extension": ".csv",
  "size_kb": 45,
  "path": "C:/Healthcare/LabResults/",
  "last_accessed": "2024-11-20"
}

✅ Prediction Output:
{
  "filename": "patient_lab_results_9926.csv",
  "sensitivity": "High",
  "sensitivity_binary": 1,
  "path": "C:/Healthcare/LabResults/",
  "confidence": 0.9994287420378456
}
