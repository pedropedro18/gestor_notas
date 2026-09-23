import pandas as pd
import os

CSV_PATH = "alunos.csv"
SEP = ";"

COLUNAS_NOTA = ["teste1", "teste2"]
COLUNAS = ["Nome", "Turma", "Nivel"] + COLUNAS_NOTA + ["presença"]


def carregar_dados():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, sep=SEP)
        for col in COLUNAS:
            if col not in df.columns:
                df[col] = "" if col in ("Nome", "Turma", "Nivel") else pd.NA
        return df
    else:
        return pd.DataFrame(columns=COLUNAS)


def guardar_dados(df):
    df.to_csv(CSV_PATH, sep=SEP, index=False)


def escolher_coluna_nota():
    print("Qual coluna?")
    for i, col in enumerate(COLUNAS_NOTA, start=1):
        print(f"{i}. {col}")
    while True:
        escolha = input("Opção: ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(COLUNAS_NOTA):
            return COLUNAS_NOTA[int(escolha) - 1]
        print("Opção inválida.")


def pesquisar_nota(df):
    nome = input("Nome do aluno a pesquisar: ").strip()
    resultado = df[df["Nome"].str.contains(nome, case=False, na=False)]

    if resultado.empty:
        print(f"\nNenhum aluno encontrado com o nome '{nome}'.\n")
        return

    print("\nResultado(s):")
    print(resultado.to_string(index=False))
    print()


def introduzir_nota(df):
    nome = input("Nome do aluno: ").strip()
    correspondencias = df[df["Nome"].str.lower() == nome.lower()]

    if correspondencias.empty:
        print(f"\nAluno '{nome}' não encontrado.")
        criar = input("Deseja adicionar este aluno? (s/n): ").strip().lower()
        if criar != "s":
            return df
        turma = input("Turma: ").strip()
        nivel = input("Nível: ").strip()
        novo = {"Nome": nome, "Turma": turma, "Nivel": nivel, "presença": obter_numero("Presença: ")}
        for col in COLUNAS_NOTA:
            novo[col] = obter_numero(f"{col}: ")
        df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
        guardar_dados(df)
        print(f"\nAluno '{nome}' adicionado.\n")
        return df

    idx = correspondencias.index[0]
    coluna = escolher_coluna_nota()
    valor = obter_numero(f"Novo valor para {coluna}: ")
    df.loc[idx, coluna] = valor
    guardar_dados(df)
    print(f"\n{coluna} de '{df.loc[idx, 'Nome']}' atualizado para {valor}.\n")
    return df


def obter_numero(mensagem):
    while True:
        valor = input(mensagem).strip()
        try:
            return float(valor)
        except ValueError:
            print("Introduza um número válido.")


def menu():
    df = carregar_dados()

    while True:
        print("=== Gestor de Notas ===")
        print("1. Pesquisar aluno")
        print("2. Introduzir / atualizar nota")
        print("3. Listar todos os alunos")
        print("4. Sair")
        escolha = input("Escolha uma opção: ").strip()

        if escolha == "1":
            pesquisar_nota(df)
        elif escolha == "2":
            df = introduzir_nota(df)
        elif escolha == "3":
            print()
            print(df.to_string(index=False) if not df.empty else "(sem alunos registados)")
            print()
        elif escolha == "4":
            print("Até já!")
            break
        else:
            print("Opção inválida.\n")


if __name__ == "__main__":
    menu()