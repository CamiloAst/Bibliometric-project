import os
import pandas as pd
import re
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import networkx as nx

# === CONFIGURACIÓN ===
DATA_FILE = "/mnt/data/unified.csv"
OUT_DIR = "outputs"
CATEGORY_MATRIX_FILE = os.path.join(OUT_DIR, "category_matrix.csv")
os.makedirs(OUT_DIR, exist_ok=True)

# === CATEGORÍAS Y VARIABLES ===
CATEGORIAS = {
    "Habilidades": [
        "Abstraction", "Algorithm", "Algorithmic thinking", "Coding", "Collaboration",
        "Cooperation", "Creativity", "Critical thinking", "Debug", "Decomposition",
        "Evaluation", "Generalization", "Logic", "Logical thinking", "Modularity",
        "Patterns recognition", "Problem solving", "Programming"
    ],
    "Conceptos Computacionales": [
        "Conditionals", "Control structures", "Directions", "Events", "Funtions", "Loops",
        "Modular structure", "Parallelism", "Sequences", "Software/hardware", "Variables"
    ],
    "Actitudes": [
        "Emotional", "Engagement", "Motivation", "Perceptions", "Persistence", "Self-efficacy",
        "Self-perceived"
    ],
    "Propiedades psicometricas": [
        "Classical Test Theory", "Confirmatory Factor Analysis", "Exploratory Factor Analysis",
        "Item Response Theory", "Reliability", "Structural Equation Model", "Validity"
    ],
    "Herramientas de evaluacion": [
        "Beginners Computational Thinking test", "Coding Attitudes Survey", "Collaborative Computing Observation Instrument",
        "Competent Computational Thinking test", "Computational thinking skills test", "Computational concepts",
        "Computational Thinking Assessment for Chinese Elementary Students", "Computational Thinking Challenge",
        "Computational Thinking Levels Scale", "Computational Thinking Scale", "Computational Thinking Skill Levels Scale",
        "Computational Thinking Test", "Computational Thinking Test for Elementary School Students",
        "Computational Thinking Test for Lower Primary", "Computational thinking-skill tasks on numbers and arithmetic",
        "Computerized Adaptive Programming Concepts Test", "CT Scale", "Elementary Student Coding Attitudes Survey",
        "General self-efficacy scale", "ICT competency test", "Instrument of computational identity",
        "KBIT fluid intelligence subtest", "Mastery of computational concepts Test and an Algorithmic Test",
        "Multidimensional 21st Century Skills Scale", "Self-efficacy scale", "STEM learning attitude scale",
        "The computational thinking scale"
    ],
    "Diseno de investigacion": [
        "No experimental", "Experimental", "Longitudinal research", "Mixed methods", "Post-test",
        "Pre-test", "Quasi-experiments"
    ],
    "Nivel de escolaridad": [
        "Upper elementary education", "Primary school", "Early childhood education", "Secondary school",
        "High school", "University"
    ],
    "Medio": [
        "Block programming", "Mobile application", "Pair programming", "Plugged activities",
        "Programming", "Robotics", "Spreadsheet", "STEM", "Unplugged activities"
    ],
    "Estrategia": [
        "Construct-by-self mind mapping", "Construct-on-scaffold mind mapping", "Design-based learning",
        "Evidence-centred design approach", "Gamification", "Reverse engineering pedagogy",
        "Technology-enhanced learning", "Collaborative learning", "Cooperative learning",
        "Flipped classroom", "Game-based learning", "Inquiry-based learning", "Personalized learning",
        "Problem-based learning", "Project-based learning", "Universal design for learning"
    ],
    "Herramienta": [
        "Alice", "Arduino", "Scratch", "ScratchJr", "Blockly Games", "Code.org", "Codecombat",
        "CSUnplugged", "Robot Turtles", "Hello Ruby", "Kodable", "LightbotJr", "KIBO robots",
        "BEE BOT", "CUBETTO", "Minecraft", "Agent Sheets", "Mimo", "Py", "SpaceChem"
    ]
}

def normalizar(text):
    return re.sub(r"[^\w\s]", "", str(text)).lower()

def crear_matriz_binaria(df, categorias):
    abstracts = df['Abstract'].fillna("").astype(str).tolist()
    matrix = []
    variables = [v for lista in categorias.values() for v in lista]
    claves = [normalizar(v.split(" - ")[0]) for v in variables]

    for abstract in abstracts:
        texto = normalizar(abstract)
        fila = [1 if k in texto else 0 for k in claves]
        matrix.append(fila)

    df_matrix = pd.DataFrame(matrix, columns=variables)
    return df_matrix

df = pd.read_csv(DATA_FILE)
matriz = crear_matriz_binaria(df, CATEGORIAS)
matriz.to_csv(CATEGORY_MATRIX_FILE, index=False)

import ace_tools as tools; tools.display_dataframe_to_user(name="Matriz de Categorías", dataframe=matriz)
