"""Parâmetros individuais da ponderada CC08, derivados somente do nome completo.

Autor: Gabriel Willian Bartmanovicz. Python 3, biblioteca padrão.
Letras acentuadas e ç contam como uma letra; espaços e pontuação não contam.
"""

import unicodedata


NOME_COMPLETO = "Gabriel Willian Bartmanovicz"
TOTAL_AMOSTRAS = 20_000
LIMITE_INATIVIDADE_S = 1.0
ATRASO_INICIAL_CONSUMIDOR_S = 0.020


def calcular_parametros(nome):
    """Calcule os parâmetros individuais pelas regras do enunciado.

    Parâmetros:
        nome (str): nome completo, incluindo partículas como "de" e "da".
    Retorno:
        dict: nome normalizado, contagens de letras, D1, D2, N, IC e m.
    Funcionamento:
        Normaliza Unicode em NFC e conta somente caracteres alfabéticos.
        D1 e D2 são os últimos dígitos das contagens; m é uma fração.
        Lança ValueError se o nome estiver vazio ou não começar por letras.
    """
    normalizado = unicodedata.normalize("NFC", nome).strip()
    if not normalizado:
        raise ValueError("Informe o nome completo da lista de chamada.")
    primeiro_nome = normalizado.split()[0]
    letras_primeiro = sum(caractere.isalpha() for caractere in primeiro_nome)
    letras_total = sum(caractere.isalpha() for caractere in normalizado)
    if letras_primeiro == 0:
        raise ValueError("O primeiro nome precisa conter letras.")
    d1 = letras_primeiro % 10
    d2 = letras_total % 10
    return {
        "nome": normalizado,
        "letras_primeiro_nome": letras_primeiro,
        "letras_nome_completo": letras_total,
        "D1": d1,
        "D2": d2,
        "N": 3 + (d2 % 5),
        "IC": 100_000 + 20_000 * d2,
        "m": 0.03 + 0.005 * d1,
    }


PARAMETROS = calcular_parametros(NOME_COMPLETO)
N = PARAMETROS["N"]
