import os
import glob
import pandas as pd

# 1) Columnas esperadas
COL_TITLE   = "Document Title"
COL_AUTHORS = "Authors"
COL_ABSTRACT= "Abstract"
COL_PDF     = "PDF Link"
COL_TERMS   = "IEEE Terms"
COL_DATE    = "Online Date"

# 2) Funciones de exportación
def export_bib(df, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        for i, row in df.iterrows():
            key     = f"ref{i+1}"
            title   = str(row[COL_TITLE])
            authors = " and ".join(a.strip() for a in str(row[COL_AUTHORS]).split(";") if a.strip())
            year    = str(row[COL_DATE])[:4]
            abstract= str(row[COL_ABSTRACT]).replace("\n", " ")
            pdf     = str(row[COL_PDF])
            terms   = str(row[COL_TERMS])

            f.write(f"@article{{{key},\n")
            f.write(f"  title     = {{{title}}},\n")
            f.write(f"  author    = {{{authors}}},\n")
            f.write(f"  year      = {{{year}}},\n")
            f.write(f"  abstract  = {{{abstract}}},\n")
            f.write(f"  keywords  = {{{terms}}},\n")
            f.write(f"  url       = {{{pdf}}},\n")
            f.write("}\n\n")

# 3) Bucle principal
if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)
    csv_files = glob.glob("data/*.csv")
    if not csv_files:
        print("⚠ No encontré ningún CSV en data/. Pon tus archivos allí.")
        exit()

    unique_titles = set()
    unique_entries = []
    duplicate_entries = []

    for csv_path in csv_files:
        name = os.path.basename(csv_path)
        print(f"→ Procesando {name} ...")
        df = pd.read_csv(csv_path).fillna('')

        missing = [c for c in [COL_TITLE, COL_AUTHORS, COL_ABSTRACT, COL_PDF, COL_TERMS, COL_DATE] if c not in df.columns]
        if missing:
            print(f"  ❌ Faltan columnas en {name}: {missing}, omitiendo este archivo.")
            continue

        for _, row in df.iterrows():
            title = str(row[COL_TITLE]).strip().lower()
            if title in unique_titles:
                duplicate_entries.append(row)
            else:
                unique_titles.add(title)
                unique_entries.append(row)

    # Crear DataFrames
    df_unique = pd.DataFrame(unique_entries)
    df_duplicates = pd.DataFrame(duplicate_entries)

    # Exportar
    export_bib(df_unique, "outputs/unified.bib")
    export_bib(df_duplicates, "outputs/duplicates.bib")

    print(f"✔ Unificados: {len(df_unique)} artículos")
    print(f"✔ Duplicados: {len(df_duplicates)} artículos")
    print("✔ Archivos generados en outputs/: unified.bib y duplicates.bib")
