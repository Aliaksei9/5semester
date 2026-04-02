import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder, MultiLabelBinarizer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

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

def linear_regression_model(X_train, X_test, y_train, y_test, metrics_list):

    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    metrics_list.append(['Linear Regression', mae, mse, rmse, r2])


def polynomial_regression_model(X_train, X_test, y_train, y_test, degree, metrics_list):

    model = make_pipeline(PolynomialFeatures(degree=degree), LinearRegression())
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    metrics_list.append([f'Polynomial Regression (degree={degree})', mae, mse, rmse, r2])


def ridge_regression_model(X_train, X_test, y_train, y_test, alpha, metrics_list):

    model = Ridge(alpha=alpha, random_state=1)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    metrics_list.append([f'Ridge Regression (alpha={alpha})', mae, mse, rmse, r2])


def lasso_regression_model(X_train, X_test, y_train, y_test, alpha, metrics_list):

    model = Lasso(alpha=alpha, random_state=1, max_iter=10000)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    metrics_list.append([f'Lasso Regression (alpha={alpha})', mae, mse, rmse, r2])


def compare_regression_models(X_train, X_test, y_train, y_test):

    metrics_list = []

    linear_regression_model(X_train, X_test, y_train, y_test, metrics_list)

    polynomial_regression_model(X_train, X_test, y_train, y_test, degree=2, metrics_list=metrics_list)

    ridge_regression_model(X_train, X_test, y_train, y_test, alpha=1.0, metrics_list=metrics_list)

    lasso_regression_model(X_train, X_test, y_train, y_test, alpha=0.1, metrics_list=metrics_list)

    results_df = pd.DataFrame(metrics_list, columns=['Модель', 'MAE', 'MSE', 'RMSE', 'R²'])
    print("\n Сравнительная таблица результатов моделей:\n")
    print(results_df.to_string(index=False))


df= pd.read_csv('Health_Risk_Dataset.csv')
df = data_preprocessing(df)
pd.set_option("display.max_columns", None)

X = df.drop(columns=['Heart_Rate', 'Patient_ID'])
y = df['Heart_Rate']

train_features, test_features, train_target, test_target = train_test_split(X, y,  test_size=0.3, random_state=42)

compare_regression_models(train_features, test_features, train_target, test_target)
