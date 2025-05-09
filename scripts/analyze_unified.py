import pandas as pd
import matplotlib.pyplot as plt
import os

# Configura rutas
input_file = "outputs/unified.csv"
output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)

# Leer CSV
df = pd.read_csv(input_file)

# ——— Limpieza de columnas clave ———
df["Authors"] = df["Authors"].fillna("")
df["FirstAuthor"] = df["Authors"].apply(lambda x: x.split(";")[0].strip() if ";" in x else x.strip())
df["Publication Year"] = pd.to_numeric(df["Publication Year"], errors="coerce")
df["Publisher"] = df["Publisher"].fillna("Desconocido")
df["Publication Title"] = df["Publication Title"].fillna("Desconocido")
df["Document Identifier"] = df["Document Identifier"].fillna("Desconocido")

# ——— Estadísticos principales ———
top_authors = df["FirstAuthor"].value_counts().head(15)
top_journals = df["Publication Title"].value_counts().head(15)
top_publishers = df["Publisher"].value_counts().head(15)
types_count = df["Document Identifier"].value_counts()

# ——— Por tipo de documento y año ———
by_type_year = df.groupby(["Document Identifier", "Publication Year"]).size().unstack(fill_value=0)

# ——— Guardar a CSV ———
top_authors.to_csv(os.path.join(output_dir, "top_authors.csv"))
top_journals.to_csv(os.path.join(output_dir, "top_journals.csv"))
top_publishers.to_csv(os.path.join(output_dir, "top_publishers.csv"))
types_count.to_csv(os.path.join(output_dir, "type_counts.csv"))
by_type_year.to_csv(os.path.join(output_dir, "type_by_year.csv"))

# ——— Graficar funciones ———
def plot_bar(series, title, filename, xlabel="Cantidad", ylabel=""):
    plt.figure(figsize=(10, 6))
    series.plot(kind="bar")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.xticks(rotation=45, ha="right")
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()

# ——— Crear gráficas ———
plot_bar(top_authors, "Top 15 Primeros Autores", "top_authors.png")
plot_bar(top_journals, "Top 15 Journals", "top_journals.png")
plot_bar(top_publishers, "Top 15 Publishers", "top_publishers.png")
plot_bar(types_count, "Cantidad por Tipo de Producto", "type_counts.png")

# ——— Gráfica por año y tipo ———
plt.figure(figsize=(12, 8))
by_type_year.T.plot(kind="bar", stacked=True)
plt.title("Documentos por Tipo y Año de Publicación")
plt.xlabel("Año")
plt.ylabel("Cantidad")
plt.legend(title="Tipo de Producto")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "type_by_year.png"))
plt.close()

print("✔ Análisis completado. Resultados guardados en la carpeta 'outputs/'")
