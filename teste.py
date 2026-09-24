"""
Exercícios de Python + Pandas — alunos.csv
Todo o código junto num só ficheiro, organizado por exercício.
Corre secção a secção (ou o ficheiro todo) para ver os resultados.
"""

import pandas as pd

# ============================================================
# PARTE 1 — Python básico
# ============================================================

# --- 1.1 ---
nome = "Pedro"
turma = "a"
print(f"O aluno {nome} está na turma {turma}.")

# --- 1.2 ---
notas = [12, 3]  # teste1, teste2
media = sum(notas) / len(notas)
print(f"Média do aluno: {media}")

# --- 1.3 ---
alunos = ["pedro", "Maria", "Ana", "João", "Sofia"]
for aluno in alunos:
    print(aluno)

# --- 1.4 ---
presenca = 4
if presenca < 3:
    print("Presença baixa")
elif presenca < 5:
    print("Presença razoável")
else:
    print("Presença boa")

# --- 1.5 ---
def media_testes(teste1, teste2):
    return (teste1 + teste2) / 2

print(media_testes(12, 3))

# --- 1.6 ---
niveis = [2, 2, 3, 1, 4, 2]
contagem_nivel4 = 0
for n in niveis:
    if n == 4:
        contagem_nivel4 += 1
print(f"Alunos de nível 4: {contagem_nivel4}")

# --- 1.7 ---
# Pede presenças ao utilizador até escrever "parar"
presencas = []
while True:
    valor = input("Presença (ou 'parar'): ")
    if valor == "parar":
        break
    presencas.append(int(valor))
print(presencas)


# ============================================================
# PARTE 2 — Introdução ao Pandas
# ============================================================

# --- 2.1 ---
df = pd.read_csv("alunos.csv", sep=";")

# --- 2.2 ---
print(df.head())
print(df.shape)

# --- 2.3 ---
print(df["Nome"])
print(df[["Nome", "Nivel"]])

# --- 2.4 ---
df["Media"] = (df["teste1"] + df["teste2"]) / 2

# --- 2.5 ---
print(f"Média geral: {df['Media'].mean()}")
print(f"Presença média: {df['presença'].mean()}")

# --- 2.6 ---
aprovados = df[df["Media"] >= 10]
print(aprovados)

# --- 2.7 ---
turma_a = df[df["Turma"] == "a"]
print(turma_a)

# --- 2.8 ---
top3 = df.sort_values("Media", ascending=False).head(3)
print(top3)

# --- 2.9 ---
print(df["Turma"].value_counts())
print(f"Valores em falta na Turma: {df['Turma'].isnull().sum()}")

# --- 2.10 (Desafio) ---
media_por_turma = df.groupby("Turma")["Media"].mean()
print(media_por_turma)

presenca_por_nivel = df.groupby("Nivel")["presença"].mean()
print(presenca_por_nivel)