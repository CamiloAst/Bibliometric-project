import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import pdist

# === CONFIGURACIÓN ===
DATA_DIR = "data"
OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# === FUNCIONES ===
def load_abstracts_from_csv(data_dir=DATA_DIR):
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    abstracts, titles = [], []
    for file in files:
        df = pd.read_csv(file)
        if 'Abstract' in df.columns and 'Document Title' in df.columns:
            for _, row in df.iterrows():
                abstract = str(row['Abstract'])
                title = str(row['Document Title'])
                if pd.notna(abstract) and pd.notna(title):
                    abstracts.append(abstract)
                    titles.append(title)
    return titles, abstracts

def preprocess_and_vectorize(abstracts):
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(abstracts)
    return X

def hierarchical_clustering(X, method="ward"):
    dist = pdist(X.toarray(), metric='cosine')  # matriz condensada
    Z = linkage(dist, method=method)
    return Z

def plot_dendrogram(Z, labels, method):
    plt.figure(figsize=(32, 18))
    plt.title(f"Dendrograma - Método: {method}")
    dendrogram(Z, labels=labels, leaf_rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, f"dendrogram_{method}.png"))
    plt.close()

# === MAIN ===
def main():
    titles, abstracts = load_abstracts_from_csv()

    if not titles:
        print("⚠ No se encontraron abstracts válidos.")
        return

    print(f"✔ Se encontraron {len(abstracts)} abstracts válidos.")

    X = preprocess_and_vectorize(abstracts)

    for method in ["ward", "average"]:
        print(f"→ Clustering con método: {method}")
        Z = hierarchical_clustering(X, method=method)
        plot_dendrogram(Z, titles, method)

    print("✔ Dendrogramas guardados en outputs/")

if __name__ == "__main__":
    main()
