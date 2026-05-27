import pandas as pd
import joblib

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

from sklearn.ensemble import VotingClassifier
from sklearn.ensemble import StackingClassifier

from sklearn.linear_model import LogisticRegression

from train_rf import train_random_forest
from train_xgb import train_xgboost
from train_lr import train_logistic_regression
from train_svm import train_svm


# -----------------------------------
# Load Dataset
# -----------------------------------

data = load_breast_cancer()

X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(data.target)

# -----------------------------------
# Train Test Split
# -----------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# -----------------------------------
# Evaluation Function
# -----------------------------------

def evaluate_model(model, X_test, y_test, model_name):

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions)
    recall = recall_score(y_test, predictions)
    f1 = f1_score(y_test, predictions)

    print(f"\n{'='*50}")
    print(f"{model_name} Performance")
    print(f"{'='*50}")

    print("Accuracy :", accuracy)
    print("Precision:", precision)
    print("Recall   :", recall)
    print("F1 Score :", f1)

    print("\nClassification Report:")
    print(classification_report(y_test, predictions))

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, predictions))


# -----------------------------------
# Train Individual Models
# -----------------------------------

rf_model = train_random_forest(X_train, y_train)

xgb_model = train_xgboost(X_train, y_train)

lr_model = train_logistic_regression(X_train, y_train)

svm_model = train_svm(X_train, y_train)

# -----------------------------------
# Evaluate Individual Models
# -----------------------------------

evaluate_model(
    rf_model,
    X_test,
    y_test,
    "Random Forest"
)

evaluate_model(
    xgb_model,
    X_test,
    y_test,
    "XGBoost"
)

evaluate_model(
    lr_model,
    X_test,
    y_test,
    "Logistic Regression"
)

evaluate_model(
    svm_model,
    X_test,
    y_test,
    "SVM"
)

# -----------------------------------
# Voting Ensemble
# -----------------------------------

voting_model = VotingClassifier(
    estimators=[
        ('rf', rf_model),
        ('xgb', xgb_model),
        ('lr', lr_model),
        ('svm', svm_model)
    ],
    voting='hard'
)

# Train Voting Ensemble
voting_model.fit(X_train, y_train)

# Evaluate Voting Ensemble
evaluate_model(
    voting_model,
    X_test,
    y_test,
    "Voting Ensemble"
)

# -----------------------------------
# Stacking Ensemble
# -----------------------------------

stacking_model = StackingClassifier(
    estimators=[
        ('rf', rf_model),
        ('xgb', xgb_model),
        ('lr', lr_model),
        ('svm', svm_model)
    ],
    final_estimator=LogisticRegression()
)

# Train Stacking Ensemble
stacking_model.fit(X_train, y_train)

# Evaluate Stacking Ensemble
evaluate_model(
    stacking_model,
    X_test,
    y_test,
    "Stacking Ensemble"
)

# -----------------------------------
# Compare Models
# -----------------------------------

model_scores = {
    "Random Forest": f1_score(y_test, rf_model.predict(X_test)),
    "XGBoost": f1_score(y_test, xgb_model.predict(X_test)),
    "Logistic Regression": f1_score(y_test, lr_model.predict(X_test)),
    "SVM": f1_score(y_test, svm_model.predict(X_test)),
    "Voting Ensemble": f1_score(y_test, voting_model.predict(X_test)),
    "Stacking Ensemble": f1_score(y_test, stacking_model.predict(X_test))
}

best_model = max(model_scores, key=model_scores.get)

print("\nBest Performing Model:", best_model)

print("Best F1 Score:", model_scores[best_model])

# -----------------------------------
# Save Best Model
# -----------------------------------

if best_model == "Random Forest":
    joblib.dump(rf_model, "best_model.pkl")

elif best_model == "XGBoost":
    joblib.dump(xgb_model, "best_model.pkl")

elif best_model == "Logistic Regression":
    joblib.dump(lr_model, "best_model.pkl")

elif best_model == "SVM":
    joblib.dump(svm_model, "best_model.pkl")

elif best_model == "Voting Ensemble":
    joblib.dump(voting_model, "best_model.pkl")

else:
    joblib.dump(stacking_model, "best_model.pkl")

print("\nBest model saved successfully!")