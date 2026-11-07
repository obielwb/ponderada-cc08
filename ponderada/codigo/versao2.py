#!/usr/bin/env python3
"""A4 — versão 2: três semáforos, vazio=N, cheio=0 e mutex=1.

Autor: Gabriel Willian Bartmanovicz. Execute: python3 ponderada/codigo/versao2.py
O produtor adquire vazio antes de mutex; o consumidor, cheio antes de mutex.
A integridade é verificada comparando toda a sequência com 0..19999.
"""

from laboratorio import executar_interface


if __name__ == "__main__":
    raise SystemExit(executar_interface(2))
