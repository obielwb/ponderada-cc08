#!/usr/bin/env python3
"""A4: execute cada versão três vezes e salve evidências reais em resultados/.

Autor: Gabriel Willian Bartmanovicz. Python 3, somente biblioteca padrão.
Cada versão roda em um subprocesso independente: threads bloqueadas em V3
não sobrevivem para contaminar a próxima experiência. Reexecutar sobrescreve
os resultados anteriores, portanto copie-os antes se quiser comparar rodadas.
"""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
import sys

from parametros import N, PARAMETROS, TOTAL_AMOSTRAS


def validar_resultados(resultados):
    """Verifique a integridade das medições e a correção da versão 2.

    Parâmetros:
        resultados (list[dict]): nove relatórios lidos dos subprocessos.
    Retorno:
        list[str]: erros encontrados; lista vazia indica validação aprovada.
    Funcionamento:
        Confere parâmetros e identidades entre métricas em todas as versões.
        Exige FIFO exato, 20.000 amostras e nenhuma perda/duplicação em V2.
        Não exige números particulares de V1 nem assume deadlock universal
        em V3: seus resultados dependem do escalonamento realmente observado.
    """
    erros = []
    if len(resultados) != 9:
        erros.append("Era necessário registrar exatamente nove execuções.")
    for resultado in resultados:
        rotulo = f"V{resultado['versao']}, execução {resultado['execucao']}"
        if resultado["planejadas"] != TOTAL_AMOSTRAS or resultado["parametros"]["N"] != N:
            erros.append(f"{rotulo}: parâmetros diferentes dos da entrega.")
        if resultado["consumidas"] != resultado["distintas"] + resultado["duplicadas"]:
            erros.append(f"{rotulo}: contagem de duplicações inconsistente.")
        if resultado["perdidas"] != TOTAL_AMOSTRAS - resultado["distintas"]:
            erros.append(f"{rotulo}: contagem de IDs ausentes inconsistente.")
        if resultado["perdidas"] != resultado["nao_produzidas"] + resultado["produzidas_nao_recebidas"]:
            erros.append(f"{rotulo}: decomposição das perdas inconsistente.")
        if resultado["erros"]:
            erros.append(f"{rotulo}: erro inesperado: {resultado['erros']}")
        if resultado["versao"] == 2:
            if not resultado["fifo_exato"] or resultado["travou"]:
                erros.append(f"{rotulo}: versão sincronizada não preservou FIFO/progresso.")
            if any(resultado[chave] != 0 for chave in ("perdidas", "duplicadas", "invalidas")):
                erros.append(f"{rotulo}: versão sincronizada corrompeu dados.")
            if resultado["consumidas"] != TOTAL_AMOSTRAS or resultado["produzidas"] != TOTAL_AMOSTRAS:
                erros.append(f"{rotulo}: versão sincronizada não entregou todas as amostras.")
    return erros


def salvar_consolidado(diretorio, resultados, erros):
    """Grave JSON e CSV consolidados e uma tabela Markdown reutilizável.

    Parâmetros:
        diretorio (Path): pasta de saída dos experimentos.
        resultados (list[dict]): relatórios completos, na ordem das execuções.
        erros (list[str]): problemas encontrados por validar_resultados.
    Retorno:
        None. Cria resultados.json, resultados.csv e tabela.md.
    Funcionamento:
        O JSON consolidado omite as sequências, já salvas nos JSON individuais.
        O CSV inclui a decomposição dos IDs ausentes e as métricas solicitadas.
        A tabela é derivada das mesmas medidas, sem arredondar contagens.
    """
    resumos = [
        {chave: valor for chave, valor in resultado.items() if chave != "sequencia_consumida"}
        for resultado in resultados
    ]
    consolidado = {
        "descricao": "Nove execuções reais da A4; uma sequência bruta por JSON individual.",
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "parametros": PARAMETROS,
        "definicoes": {
            "consumidas": "Leituras válidas; inclui repetições do mesmo ID.",
            "perdidas": "IDs de 0..19999 não recebidos; inclui os não produzidos até o encerramento.",
            "duplicadas": "Repetições além da primeira ocorrência de cada ID válido.",
            "travou": "Watchdog observou um segundo sem nova leitura do consumidor.",
        },
        "validacao": {"aprovada": not erros, "erros": erros},
        "execucoes": resumos,
    }
    (diretorio / "resultados.json").write_text(
        json.dumps(consolidado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    campos = [
        "versao", "execucao", "planejadas", "produzidas", "consumidas", "distintas",
        "perdidas", "duplicadas", "invalidas", "nao_produzidas", "produzidas_nao_recebidas",
        "travou", "fifo_exato", "duracao_s", "ocupadas_final",
    ]
    with (diretorio / "resultados.csv").open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(resultados)
    linhas = [
        "# A4 — resultados de execuções reais",
        "",
        f"Cada execução tentou {TOTAL_AMOSTRAS} amostras, com N={N}. Perdidas são IDs ausentes do universo planejado.",
        "",
        "| Versão | Execução | Produzidas | Consumidas | Perdidas | Duplicadas | Inválidas | Travou? |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for r in resultados:
        linhas.append(
            f"| {r['versao']} | {r['execucao']} | {r['produzidas']} | {r['consumidas']} | "
            f"{r['perdidas']} | {r['duplicadas']} | {r['invalidas']} | {'Sim' if r['travou'] else 'Não'} |"
        )
    linhas.extend(["", "Validação: " + ("APROVADA" if not erros else "FALHOU"), ""])
    (diretorio / "tabela.md").write_text("\n".join(linhas), encoding="utf-8")


def main():
    """Execute a bateria completa e apresente o local das evidências.

    Parâmetros:
        Nenhum. Os parâmetros individuais são importados de parametros.py.
    Retorno:
        int: 0 quando a bateria e a validação terminaram; 1 em caso de falha.
    Funcionamento:
        Executa V1, V2 e V3 três vezes, sequencialmente, com 20.000 amostras.
        Salva stdout/stderr e JSON de cada processo; timeout de 180 s protege
        somente o executor contra erro inesperado, não substitui o watchdog.
    """
    base = Path(__file__).resolve().parent
    diretorio = base / "resultados"
    diretorio.mkdir(exist_ok=True)
    resultados = []
    for versao in (1, 2, 3):
        for repeticao in (1, 2, 3):
            nome = f"versao{versao}_execucao{repeticao}"
            relativo = Path("resultados") / f"{nome}.json"
            comando = [sys.executable, f"versao{versao}.py", "--json", str(relativo)]
            print(f"Executando V{versao}, repetição {repeticao}/3...", flush=True)
            concluido = subprocess.run(
                comando, cwd=base, capture_output=True, text=True, encoding="utf-8", timeout=180
            )
            log = f"A4 — execução {repeticao}/3 da versão {versao}\n$ {shlex.join(comando)}\n\n{concluido.stdout}"
            if concluido.stderr:
                log += "\nSTDERR:\n" + concluido.stderr
            (diretorio / f"{nome}.txt").write_text(log, encoding="utf-8")
            if concluido.returncode != 0:
                print(f"Falha; consulte {diretorio / (nome + '.txt')}", file=sys.stderr)
                return 1
            resultado = json.loads((base / relativo).read_text(encoding="utf-8"))
            resultado["execucao"] = repeticao
            resultado["arquivo_dados"] = str(relativo)
            resultado["arquivo_log"] = str(Path("resultados") / f"{nome}.txt")
            resultados.append(resultado)
            print(
                f"  consumidas={resultado['consumidas']}, perdidas={resultado['perdidas']}, "
                f"duplicadas={resultado['duplicadas']}, travou={resultado['travou']}", flush=True
            )
    erros = validar_resultados(resultados)
    salvar_consolidado(diretorio, resultados, erros)
    print(f"\nEvidências: {diretorio}")
    print("Validação: " + ("APROVADA" if not erros else "FALHOU"))
    for erro in erros:
        print("- " + erro)
    return 1 if erros else 0


if __name__ == "__main__":
    raise SystemExit(main())
