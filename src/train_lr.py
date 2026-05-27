from sklearn.linear_model import LogisticRegression

def train_logistic_regression(X_train, y_train):

    lr_model = LogisticRegression(max_iter=1000)

    lr_model.fit(X_train, y_train)

    return lr_model