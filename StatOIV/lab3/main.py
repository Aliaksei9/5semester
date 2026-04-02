import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, ConfusionMatrixDisplay, classification_report
)

CSV_PATH = 'Health_Risk_Dataset.csv'
OUT_DIR = 'classification_outputs'
RANDOM_STATE = 42
TEST_SIZE = 0.2

os.makedirs(OUT_DIR, exist_ok=True)


def data_preprocessing(df)->object:
    df_filled = df.copy()

    df_filled['Risk_Level'] = df_filled['Risk_Level'].astype('category')
    df_filled['On_Oxygen'] = df_filled['On_Oxygen'].astype('category')
    df_filled['Consciousness'] = df_filled['Consciousness'].astype('category')

    numeric_cols = df_filled.select_dtypes(include=['float64', 'int64']).columns

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df_filled[numeric_cols])

    imputer = KNNImputer(n_neighbors=10)
    imputed_data = imputer.fit_transform(scaled_data)

    df_filled[numeric_cols] = imputed_data

    categories_consciousness = [["A", "P", "C", "V", "U"]]
    encoder_consciousness = OrdinalEncoder(categories=categories_consciousness)
    df_filled["Consciousness"] = encoder_consciousness.fit_transform(df_filled[["Consciousness"]])

    # Risk_Level — Ordinal Encoding
    categories_risk = [["Low", "Normal", "Medium", "High"]]
    encoder_risk = OrdinalEncoder(categories=categories_risk)
    df_filled["Risk_Level"] = encoder_risk.fit_transform(df_filled[["Risk_Level"]])


    feature = np.array(df_filled[["On_Oxygen"]])

    one_hot = OneHotEncoder(sparse_output=False)
    encoded_feature = one_hot.fit_transform(feature)

    new_cols = one_hot.get_feature_names_out(["On_Oxygen"])

    encoded_df = pd.DataFrame(encoded_feature, columns=new_cols, index=df_filled.index)

    df_filled = pd.concat([df_filled.drop(columns=["On_Oxygen"]), encoded_df], axis=1)

    Q1 = df_filled['Heart_Rate'].quantile(0.25)
    Q3 = df_filled['Heart_Rate'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    df_filled = df_filled[(df_filled['Heart_Rate'] >= lower_bound) & (df_filled['Heart_Rate'] <= upper_bound)]
    return df_filled


def save_confusion_matrix(y_true, y_pred, labels, display_labels, out_dir, model_name):
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=display_labels)
    fig, ax = plt.subplots(figsize=(6, 5))
    disp.plot(ax=ax, include_values=True)
    ax.set_title(f"Confusion Matrix — {model_name}")
    plt.tight_layout()
    safe = model_name.replace(' ', '_').replace('(', '').replace(')', '').replace('=', '')
    path = os.path.join(out_dir, f"confusion_matrix_{safe}.png")
    fig.savefig(path)
    plt.close(fig)
    return path


def compute_metrics(y_true, y_pred, y_proba=None):
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
    recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
    roc_auc = np.nan
    roc_auc = roc_auc_score(y_true, y_proba, multi_class='ovr', average='macro')

    return accuracy, precision, recall, f1, roc_auc


def decision_tree_model(X_train, X_test, y_train, y_test, metrics_list, out_dir=OUT_DIR):
    name = "Decision Tree"
    model = DecisionTreeClassifier(random_state=RANDOM_STATE)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

    acc, prec, rec, f1, roc_auc = compute_metrics(y_test, y_pred, y_proba)
    metrics_list.append([name, acc, prec, rec, f1, roc_auc])

    save_confusion_matrix(y_test, y_pred, labels=[0,1,2,3], display_labels=['Low','Normal','Medium','High'], out_dir=out_dir, model_name=name)
    return model


def knn_model(X_train, X_test, y_train, y_test, metrics_list, n_neighbors=5, out_dir=OUT_DIR):
    name = f"KNN (k={n_neighbors})"
    model = KNeighborsClassifier(n_neighbors=n_neighbors)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

    acc, prec, rec, f1, roc_auc = compute_metrics(y_test, y_pred, y_proba)
    metrics_list.append([name, acc, prec, rec, f1, roc_auc])

    save_confusion_matrix(y_test, y_pred, labels=[0,1,2,3], display_labels=['Low','Normal','Medium','High'], out_dir=out_dir, model_name=name)

    return model


def logistic_regression_model(X_train, X_test, y_train, y_test, metrics_list, out_dir=OUT_DIR):
    name = "Logistic Regression"
    model = LogisticRegression(max_iter=2000, multi_class='multinomial', solver='lbfgs', random_state=RANDOM_STATE)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

    acc, prec, rec, f1, roc_auc = compute_metrics(y_test, y_pred, y_proba)
    metrics_list.append([name, acc, prec, rec, f1, roc_auc])

    save_confusion_matrix(y_test, y_pred, labels=[0,1,2,3], display_labels=['Low','Normal','Medium','High'], out_dir=out_dir, model_name=name)


    return model


def gaussian_nb_model(X_train, X_test, y_train, y_test, metrics_list, out_dir=OUT_DIR):
    name = "Gaussian NB"
    model = GaussianNB()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

    acc, prec, rec, f1, roc_auc = compute_metrics(y_test, y_pred, y_proba)
    metrics_list.append([name, acc, prec, rec, f1, roc_auc])

    save_confusion_matrix(y_test, y_pred, labels=[0,1,2,3], display_labels=['Low','Normal','Medium','High'], out_dir=out_dir, model_name=name)

    return model


def compare_classification_models(X_train, X_test, y_train, y_test, out_dir=OUT_DIR):
    metrics_list = []
    models = {}
    models['Decision Tree'] = decision_tree_model(X_train, X_test, y_train, y_test, metrics_list, out_dir=out_dir)
    models['KNN'] = knn_model(X_train, X_test, y_train, y_test, metrics_list, n_neighbors=5, out_dir=out_dir)
    models['Logistic Regression'] = logistic_regression_model(X_train, X_test, y_train, y_test, metrics_list, out_dir=out_dir)
    models['Gaussian NB'] = gaussian_nb_model(X_train, X_test, y_train, y_test, metrics_list, out_dir=out_dir)

    df_results = pd.DataFrame(metrics_list, columns=['Model', 'Accuracy', 'Precision_macro', 'Recall_macro', 'F1_macro', 'ROC_AUC_macro_ovr'])
    df_results = df_results.set_index('Model').round(4)
    print("\nСравнительная таблица метрик (включая Accuracy):\n")
    print(df_results.to_string())
    return df_results, models


def main():
    if not os.path.isfile(CSV_PATH):
        raise FileNotFoundError(f"CSV файл не найден по пути: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    print("Исходный размер датасета:", df.shape)

    df_proc = data_preprocessing(df)
    print("Размер после предобработки:", df_proc.shape)


    df_proc = df_proc.drop(columns=['Patient_ID'])

    X = df_proc.drop(columns=['Risk_Level'])
    y = df_proc['Risk_Level'].values


    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE)

    print("Train:", X_train.shape, "Test:", X_test.shape)
    df_results, trained_models = compare_classification_models(X_train, X_test, y_train, y_test, out_dir=OUT_DIR)


if __name__ == '__main__':
    main()
