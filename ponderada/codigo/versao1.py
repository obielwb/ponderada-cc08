#!/usr/bin/env python3
"""A4 — versão 1: contador sem sincronização, espera ocupada e sleep(0).

Autor: Gabriel Willian Bartmanovicz. Execute: python3 ponderada/codigo/versao1.py
O watchdog registra travamento após 1 s sem consumo. O resultado pode variar
com o escalonamento; perdas e duplicações são calculadas, nunca presumidas.
"""

from laboratorio import executar_interface


if __name__ == "__main__":
    raise SystemExit(executar_interface(1))
