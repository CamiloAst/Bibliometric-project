import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import os

# === CARGA DE DATOS ===
df = pd.read_csv("outputs/unified.csv")
df.columns = df.columns.str.strip().str.lower()
df = df.dropna(subset=["abstract"])
abstracts = df["abstract"].tolist()

# === CARPETA DE SALIDA ===
output_dir = "outputs/clusters"
os.makedirs(output_dir, exist_ok=True)

# === TF-IDF + COSENO ===
print("Calculando clusters con TF-IDF + Coseno...")
tfidf = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf.fit_transform(abstracts)
cosine_sim_matrix = cosine_similarity(tfidf_matrix)
linkage_tfidf = linkage(1 - cosine_sim_matrix, method="ward")
clusters_tfidf = fcluster(linkage_tfidf, t=10, criterion="maxclust")
df["cluster_tfidf"] = clusters_tfidf

# === BINARIO + JACCARD ===
print("Calculando clusters con Jaccard...")
vectorizer = CountVectorizer(stop_words="english", binary=True)
binary_matrix = vectorizer.fit_transform(abstracts)
jaccard_dist = pdist(binary_matrix.toarray(), metric="jaccard")
linkage_jaccard = linkage(jaccard_dist, method="ward")
clusters_jaccard = fcluster(linkage_jaccard, t=10, criterion="maxclust")
df["cluster_jaccard"] = clusters_jaccard

# === EXPORTA RESULTADO GLOBAL ===
df.to_csv("outputs/clusters/clusters_tfidf.csv", index=False)
print("Guardado archivo general: clusters_tfidf.csv")

# === EXPORTA POR CLUSTER ===
print("Exportando archivos por cluster...")

for method in ["tfidf", "jaccard"]:
    col = f"cluster_{method}"
    for cluster_id in sorted(df[col].unique()):
        subset = df[df[col] == cluster_id]
        filename = f"{output_dir}/cluster_{method}_{cluster_id}.csv"
        subset.to_csv(filename, index=False)

print(f"Archivos exportados por cluster en: {output_dir}")

# === DENDROGRAMAS ===
plt.figure(figsize=(12, 6))
dendrogram(linkage_tfidf, labels=clusters_tfidf, orientation='top', distance_sort='descending', no_labels=True)
plt.title("Dendrograma - TF-IDF + Cosine Similarity")
plt.tight_layout()
plt.savefig("outputs/clusters/dendrograma_tfidf_coseno.png")
plt.close()

plt.figure(figsize=(12, 6))
dendrogram(linkage_jaccard, labels=clusters_jaccard, orientation='top', distance_sort='descending', no_labels=True)
plt.title("Dendrograma - CountVectorizer + Jaccard Distance")
plt.tight_layout()
plt.savefig("outputs/clusters/dendrograma_jaccard.png")
plt.close()

print("¡Dendrogramas y CSVs por cluster generados exitosamente!")
