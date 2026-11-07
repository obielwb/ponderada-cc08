# Tato — Ponderada Computação CC08

**Autor: Gabriel Willian Bartmanovicz.**

Análise de arquitetura, memória, pipeline, concorrência e deadlock de uma pulseira sensorial, com experimentos em Python e uma decisão de produção.

## Trabalho

Leia [ponderada/ponderada-tato.md](ponderada/ponderada-tato.md), com as Partes A e B, contas, diagramas e resultados.

O nome completo foi confirmado conforme a lista de chamada: Gabriel (7), Willian (7) e Bartmanovicz (12), totalizando **26 letras**. Assim, **D1 = 7, D2 = 6, N = 4, IC = 220.000 instruções/amostra e m = 6,5%**.

| Configuração | Tempo considerado | Cumpre 5 ms no modelo? |
| --- | ---: | --- |
| H | 6,875 ms | Não |
| V, incluindo até 3 ms do Linux | 5,042333 ms | Não no pior caso do modelo |
| H com DSP | 3,575 ms | Sim; margem de 1,425 ms |

## Executar a questão A4

Requer **Python 3.10 ou superior**, sem dependências externas. Na raiz deste repositório, execute um comando por versão:

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

Cada comando tenta produzir **20.000 amostras, de 0 a 19.999**, com buffer circular de **4 posições**. A saída informa consumidas, perdidas, duplicadas e travamento.

| Versão | Algoritmo | Comportamento investigado |
| --- | --- | --- |
| 1 | Contador compartilhado sem proteção, espera ocupada e `time.sleep(0)` entre leitura e escrita | Corrida, perdas, duplicações e possível travamento. |
| 2 | `vazio = 4`, `cheio = 0`, `mutex = 1`; produtor adquire vazio antes de mutex | Entrega FIFO completa sem perdas nem duplicações. |
| 3 | Mesmos semáforos; produtor adquire mutex antes de vazio | Deadlock ao preencher o buffer, mantendo o mutex. |

**Os defeitos das versões 1 e 3 são intencionais e exigidos pelo exercício.** Todas usam a mesma pausa inicial de 20 ms no consumidor para exercitar o buffer cheio. A produção ocorre tão rapidamente quanto possível; o experimento investiga concorrência, sem simular os 100 Hz ou demonstrar os 5 ms do produto.

O watchdog registra travamento após **1 segundo sem consumo**, com trabalho pendente. A coleta também termina ao atingir 20.000 leituras, mesmo com duplicatas. Por isso, o relatório verifica identificadores distintos e compara toda a sequência da versão 2 com `list(range(20000))`.

**Perdidas** significa identificadores esperados ausentes, incluindo os ainda não produzidos. Os resultados separam não produzidas de produzidas não recebidas. Encerrar o processo do teste libera a sessão, mas não recupera o algoritmo em deadlock. Os números da versão 1 variam com o escalonamento.

## Reproduzir a bateria de testes

```bash
python3 ponderada/codigo/executar_experimentos.py
```

O executor inicia cada versão três vezes, em processos separados, e valida as métricas e o FIFO da versão 2. Os nove TXT e JSON individuais, sequências brutas, consolidado JSON, CSV e tabela Markdown ficam em [ponderada/codigo/resultados](ponderada/codigo/resultados/).

**Executar novamente sobrescreve essa rodada.** Antes de entregar outra rodada, atualize também a tabela A4.3 e os prints com os novos dados. A versão 1 pode demorar alguns minutos por repetição devido à espera ocupada e ao escalonamento do Python no macOS; o watchdog mede inatividade, não a duração total.

## Evidências da máquina e dos experimentos

As caches e as nove execuções entregues foram coletadas no **Mac do autor, Apple M2, macOS 26.6.2, arm64**. Os JSON identificam a versão efetiva do Python, o sistema e o horário UTC de cada execução. A data local da coleta é **06/11/2026, America/Sao_Paulo**.

- [Caches do Mac](ponderada/img/cache_macos.png) e [saída textual dos comandos](ponderada/img/cache_macos.txt).
- [Print da versão 1](ponderada/img/versao1_execucao1.png), [versão 2](ponderada/img/versao2_execucao1.png) e [versão 3](ponderada/img/versao3_execucao1.png).

Os prints são **capturas do navegador local exibindo os registros reais**, identificados no relatório e mantidos em TXT para conferência. Não são capturas do aplicativo Terminal. Os diagramas de pipeline, estados e deadlock são figuras didáticas geradas pelo código.

A coleta da cache usa `sysctl -a | grep cachesize`, complementado por `hw.perflevel` para distinguir os núcleos Performance e Efficiency. A seção A1.5 apresenta as capacidades e a justificativa da classificação da arquitetura.

## Recriar os diagramas — opcional

Os cinco diagramas estão prontos. Para recriá-los, use um Python com Pillow instalado:

```bash
python3 -m pip install Pillow
python3 ponderada/codigo/gerar_figuras.py
```

O auxiliar gera apenas os diagramas e **preserva os prints reais**. Pillow não é necessário para executar a A4.

## Organização e entrega

| Caminho | Conteúdo |
| --- | --- |
| `README.md` | Identificação e execução. |
| `.gitignore` | Exclusão de caches e arquivos locais. |
| `ponderada/ponderada-tato.md` | Resolução A1–A5 e memorando da Parte B. |
| `ponderada/codigo/` | Três versões, parâmetros, executor e gerador dos diagramas. |
| `ponderada/codigo/resultados/` | Nove execuções reais e métricas verificáveis. |
| `ponderada/img/` | Capturas das evidências e diagramas. |

Repositório: [obielwb/ponderada-cc08](https://github.com/obielwb/ponderada-cc08).

A tag de entrega é **PONDERADA-CC08**, criada na data efetiva de publicação e apontando para o commit final. Para verificar o destino:

```bash
git ls-remote origin refs/heads/main 'refs/tags/PONDERADA-CC08*'
```

O ZIP contém os arquivos do trabalho, sem metadados internos do Git, caches Python ou ambientes virtuais.
