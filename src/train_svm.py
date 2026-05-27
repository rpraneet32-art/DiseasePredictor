from sklearn.svm import SVC

def train_svm(X_train, y_train):

    svm_model = SVC(probability=True)

    svm_model.fit(X_train, y_train)

    return svm_model