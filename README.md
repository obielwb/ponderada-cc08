# Ponderada Computação CC08

**Gabriel Willian Bartmanovicz**

Resolução da atividade sobre a pulseira sensorial da Tato, com contas de arquitetura e pipeline, experimentos de concorrência e uma decisão de produção.

O trabalho completo está em [ponderada/ponderada-tato.md](ponderada/ponderada-tato.md), com as Partes A e B. Tato é a startup fictícia do enunciado.

Meu nome tem 26 letras: Gabriel (7), Willian (7) e Bartmanovicz (12). Os parâmetros são **D1 = 7, D2 = 6, N = 4, IC = 220.000 e m = 6,5%**.

## Rodar as três versões da A4

Use **Python 3.10 ou superior**, sem instalar bibliotecas externas. Abra o terminal na raiz do repositório e escolha uma versão:

```bash
python3 ponderada/codigo/versao1.py
```

```bash
python3 ponderada/codigo/versao2.py
```

```bash
python3 ponderada/codigo/versao3.py
```

No Windows, se necessário, substitua `python3` por `py -3`.

Cada teste usa um buffer de **4 posições** e meta de **20.000 amostras**, numeradas de 0 a 19.999. A saída mostra consumidas, perdidas, duplicadas e se houve travamento.

- **Versão 1:** contador sem proteção, espera ocupada e `time.sleep(0)` entre leitura e escrita. A corrida é intencional.
- **Versão 2:** semáforos `vazio = 4`, `cheio = 0` e `mutex = 1`, com aquisição na ordem correta.
- **Versão 3:** produtor adquire `mutex` antes de `vazio`, permitindo o deadlock pedido na atividade.

Todas usam a mesma pausa inicial de 20 ms no consumidor. O watchdog encerra a coleta após 1 segundo sem consumo; também há encerramento ao atingir 20.000 leituras. A seção A4 explica por que essa contagem, sozinha, não garante a entrega correta e como as perdas são contabilizadas. Os testes avaliam concorrência, sem medir o prazo de 5 ms da pulseira.

## Repetir a rodada completa

```bash
python3 ponderada/codigo/executar_experimentos.py
```

O executor roda cada versão três vezes em processos separados. Os [resultados](ponderada/codigo/resultados/) incluem os nove logs, JSON com as sequências completas, um consolidado, CSV e tabela Markdown. A versão 2 também é verificada pela sequência FIFO completa.

Esse comando **sobrescreve os resultados**. Se fizer outra rodada, atualize a tabela A4.3 e os prints com ela. Na versão 1, cada repetição pode levar alguns minutos por causa da espera ocupada e do escalonamento do Python; o watchdog mede inatividade, não o tempo total.

## Máquina e evidências

A coleta das caches e os nove testes foram feitos no meu **Mac com Apple M2, macOS 26.6.2, arm64**, em **06/11/2026, no horário de São Paulo**. Os JSON guardam a versão do Python, o sistema e o horário UTC de cada execução.

- [Caches do Mac](ponderada/img/cache_macos.png) e [saída dos comandos](ponderada/img/cache_macos.txt).
- Prints da primeira execução de cada versão: [V1](ponderada/img/versao1_execucao1.png), [V2](ponderada/img/versao2_execucao1.png) e [V3](ponderada/img/versao3_execucao1.png).

Os prints mostram os registros reais abertos no navegador local. A captura direta do aplicativo Terminal ficou indisponível. Os diagramas de pipeline, estados e deadlock são figuras didáticas.

## Recriar os diagramas

Os cinco diagramas já estão em `ponderada/img/`. Para gerá-los novamente, instale Pillow no Python que usar:

```bash
python3 -m pip install Pillow
python3 ponderada/codigo/gerar_figuras.py
```

O auxiliar preserva os prints. Pillow é usado somente nos diagramas; as três versões da A4 funcionam com a biblioteca padrão.

## Entrega

O relatório fica em `ponderada/ponderada-tato.md`, o código e os resultados em `ponderada/codigo/`, e as imagens em `ponderada/img/`.

Repositório: [obielwb/ponderada-cc08](https://github.com/obielwb/ponderada-cc08).

A tag **PONDERADA-CC08** registra a publicação inicial. A revisão da redação, com os mesmos resultados e arquivos de código, está em **PONDERADA-CC08-REVISAO-1** e na branch `main`. Para conferir:

```bash
git ls-remote origin refs/heads/main 'refs/tags/PONDERADA-CC08*'
```

O ZIP contém os arquivos do trabalho, sem `.git`, caches Python ou ambientes virtuais.
