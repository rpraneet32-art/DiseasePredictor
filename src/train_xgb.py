from xgboost import XGBClassifier

def train_xgboost(X_train, y_train):

    xgb_model = XGBClassifier(
        eval_metric='logloss',
        random_state=42
    )

    xgb_model.fit(X_train, y_train)

    return xgb_model

