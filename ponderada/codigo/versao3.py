#!/usr/bin/env python3
"""A4 — versão 3: produtor adquire mutex antes de vazio, podendo travar.

Autor: Gabriel Willian Bartmanovicz. Execute: python3 ponderada/codigo/versao3.py
Todo o restante é igual à versão 2. O watchdog observa o bloqueio e encerra
o processo de teste, sem liberar à força os semáforos que causaram deadlock.
"""

from laboratorio import executar_interface


if __name__ == "__main__":
    raise SystemExit(executar_interface(3))
