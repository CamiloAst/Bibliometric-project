# merge_csvs.py

import os
import glob
import pandas as pd

# Ruta de entrada y salida
DATA_DIR = "data"
OUT_PATH = "outputs/unified.csv"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

# Buscar todos los CSV en la carpeta
csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))

# Leer y combinar todos los CSV
dfs = []
for file in csv_files:
    try:
        df = pd.read_csv(file)
        dfs.append(df)
        print(f"✔ Cargado: {os.path.basename(file)}")
    except Exception as e:
        print(f"❌ Error al cargar {file}: {e}")

# Concatenar y limpiar
if dfs:
    df_final = pd.concat(dfs, ignore_index=True)
    df_final.dropna(how='all', inplace=True)  # Elimina filas completamente vacías
    df_final.to_csv(OUT_PATH, index=False)
    print(f"\n✅ Archivo unificado guardado en: {OUT_PATH}")
else:
    print("⚠ No se encontraron archivos CSV válidos.")
