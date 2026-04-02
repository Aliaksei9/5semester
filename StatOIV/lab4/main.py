import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, OrdinalEncoder, OneHotEncoder
from sklearn.impute import KNNImputer
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.neighbors import NearestNeighbors
import scipy.cluster.hierarchy as sch

CSV_PATH = 'Health_Risk_Dataset.csv'
OUT_DIR = 'clustering_outputs'
os.makedirs(OUT_DIR, exist_ok=True)

def data_preprocessing(df):
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

    # Risk_Level — Ordinal Encoding (but we'll drop it for clustering)
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

def save_plot(fig, name):
    path = os.path.join(OUT_DIR, f"{name}.png")
    fig.savefig(path)
    plt.close(fig)
    return path

def kmeans_clustering(X_scaled):
    # Elbow Method
    inertias = []
    for k in range(1, 11):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
    fig, ax = plt.subplots()
    ax.plot(range(1, 11), inertias, marker='o')
    ax.set_title("Elbow Method for KMeans")
    save_plot(fig, "elbow_kmeans")

    # Silhouette Analysis
    sil_scores = []
    for k in range(2, 11):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        sil_scores.append(silhouette_score(X_scaled, kmeans.labels_))
    fig, ax = plt.subplots()
    ax.plot(range(2, 11), sil_scores, marker='o')
    ax.set_title("Silhouette Scores for KMeans")
    save_plot(fig, "silhouette_kmeans")

    # Choose optimal k
    optimal_k = np.argmax(sil_scores) + 2
    print(f"Optimal K for KMeans: {optimal_k}")
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    return labels, optimal_k, "KMeans"

def agglomerative_clustering(X_scaled):
    linkage = 'ward'

    # Dendrogram
    fig, ax = plt.subplots(figsize=(10, 7))
    dend = sch.dendrogram(sch.linkage(X_scaled, method=linkage))
    ax.set_title(f"Dendrogram - Agglomerative ({linkage})")
    save_plot(fig, f"dendrogram_agglomerative_{linkage}")

    # Choose n_clusters
    n_clusters_agg = 2  # Adjust based on dendrogram
    print(f"Chosen clusters for Agglomerative: {n_clusters_agg}")
    agg = AgglomerativeClustering(n_clusters=n_clusters_agg, linkage=linkage)
    labels = agg.fit_predict(X_scaled)
    return labels, n_clusters_agg, "Agglomerative"


def dbscan_clustering(X_scaled):
    min_samples = 2 * X_scaled.shape[1]
    nbrs = NearestNeighbors(n_neighbors=min_samples).fit(X_scaled)
    distances = nbrs.kneighbors(X_scaled)[0]
    dist_sorted = np.sort(distances[:, min_samples - 1], axis=0)
    fig, ax = plt.subplots()
    ax.plot(dist_sorted)
    ax.set_title("k-Distance Graph for DBSCAN")
    save_plot(fig, "k_distance_dbscan")

    eps = 0.8 # Adjust based on plot
    print(f"Chosen eps: {eps}, min_samples: {min_samples}")
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(X_scaled)

    # Calculate and print the number of outliers
    n_outliers = np.sum(labels == -1)
    print(f"Number of outliers: {n_outliers}")

    n_clusters_db = len(np.unique(labels)) - 1 if -1 in labels else len(np.unique(labels))
    return labels, n_clusters_db, "DBSCAN"

def evaluate_clustering_quality(X, labels, model_name):

    if len(np.unique(labels)) < 2:
        print(f"{model_name} - Not enough clusters for metrics.")
        return np.nan, np.nan, np.nan

    sil = silhouette_score(X, labels)
    db = davies_bouldin_score(X, labels)
    ch = calinski_harabasz_score(X, labels)
    return sil, db, ch

def analyze_clustering_results(X, labels, model_name, features):
    # 2D Projection with PCA
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)
    fig, ax = plt.subplots()
    sns.scatterplot(x=X_pca[:, 0], y=X_pca[:, 1], hue=labels, palette='viridis', ax=ax)
    ax.set_title(f"PCA 2D Projection - {model_name}")
    save_plot(fig, f"pca_{model_name}")

    # Histogram of cluster sizes
    fig, ax = plt.subplots()
    pd.Series(labels).value_counts().plot.bar(ax=ax)
    ax.set_title(f"Cluster Sizes - {model_name}")
    save_plot(fig, f"cluster_sizes_{model_name}")

    # Boxplots for features
    df = pd.DataFrame(X, columns=features)
    df['cluster'] = labels
    for feature in features:
        fig, ax = plt.subplots()
        sns.boxplot(x='cluster', y=feature, data=df, ax=ax)
        ax.set_title(f"Boxplot {feature} by Cluster - {model_name}")
        save_plot(fig, f"boxplot_{feature}_{model_name}")

if __name__ == '__main__':
    df = pd.read_csv(CSV_PATH)
    print("Original dataset shape:", df.shape)

    df_proc = data_preprocessing(df)
    print("Processed dataset shape:", df_proc.shape)

    # For clustering, exclude Patient_ID and Risk_Level
    X = df_proc.drop(columns=['Patient_ID', 'On_Oxygen_0', 'On_Oxygen_1','Oxygen_Saturation', 'O2_Scale', 'Consciousness'])
    #"Temperature", "Consciousness", "Heart_Rate"
    features = X.columns.tolist()

    # Standardize X
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    results = []

    # KMeans
    kmeans_labels, optimal_k, model_name = kmeans_clustering(X_scaled)
    sil, db, ch = evaluate_clustering_quality(X_scaled, kmeans_labels, model_name)
    results.append([model_name, optimal_k, sil, db, ch])
    analyze_clustering_results(X_scaled, kmeans_labels, model_name, features)

    # Agglomerative
    agg_labels, n_clusters_agg, model_name = agglomerative_clustering(X_scaled)
    sil, db, ch = evaluate_clustering_quality(X_scaled, agg_labels, model_name)
    results.append([model_name, n_clusters_agg, sil, db, ch])
    analyze_clustering_results(X_scaled, agg_labels, model_name, features)

    # DBSCAN
    dbscan_labels, n_clusters_db, model_name = dbscan_clustering(X_scaled)
    mask = dbscan_labels != -1
    sil, db, ch = evaluate_clustering_quality(X_scaled[mask], dbscan_labels[mask], model_name)
    results.append([model_name, n_clusters_db, sil, db, ch])
    analyze_clustering_results(X_scaled, dbscan_labels, model_name, features)

    # Final table
    df_results = pd.DataFrame(results, columns=['Algorithm', 'Number of Clusters', 'Silhouette', 'Davies-Bouldin',
                                                    'Calinski-Harabasz'])
    df_results = df_results.set_index('Algorithm').round(4)
    print("\nOverall Clustering Results:\n")
    print(df_results.to_string())