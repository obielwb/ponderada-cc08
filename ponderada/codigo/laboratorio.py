"""A4: buffer circular em três versões e observação de concorrência real.

Autor: Gabriel Willian Bartmanovicz. Python 3, somente biblioteca padrão.
As versões 2 e 3 usam os mesmos três semáforos e diferem exclusivamente na
ordem das duas aquisições do produtor. O watchdog observa a falta de consumo;
ele não libera semáforos nem desfaz o deadlock. Cada execução é um processo.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import threading
import time

from parametros import (
    ATRASO_INICIAL_CONSUMIDOR_S,
    LIMITE_INATIVIDADE_S,
    N,
    PARAMETROS,
    TOTAL_AMOSTRAS,
)


class Estado:
    """Estado do experimento; somente a versão 1 acessa o buffer sem proteção."""

    def __init__(self, versao, total, atraso_consumidor):
        """Inicialize o buffer, a instrumentação e os semáforos aplicáveis.

        Parâmetros:
            versao (int): 1, 2 ou 3; seleciona o algoritmo estudado.
            total (int): quantidade de amostras que o produtor tentará gerar.
            atraso_consumidor (float): pausa inicial, em segundos, do consumidor.
        Retorno:
            None. Os atributos ficam disponíveis para as duas threads.
        Funcionamento:
            Event apenas comunica encerramento; não protege contador ou buffer.
            Nas versões 2 e 3, vazio=N, cheio=0 e mutex=1 são os três semáforos.
            A versão 1 não cria nenhum semáforo de aplicação.
        """
        self.versao = versao
        self.total = total
        self.atraso_consumidor = atraso_consumidor
        self.buffer = [None] * N
        self.escrita = 0
        self.leitura = 0
        self.ocupadas = 0
        self.produzidas = 0
        self.consumidas = []
        self.parar = threading.Event()
        self.produtor_terminou = False
        self.consumidor_terminou = False
        self.produtor_estado = "ainda não iniciou"
        self.consumidor_estado = "ainda não iniciou"
        self.ultimo_consumo = time.monotonic()
        self.erros = []
        if versao in (2, 3):
            self.vazio = threading.Semaphore(N)
            self.cheio = threading.Semaphore(0)
            self.mutex = threading.Semaphore(1)


def produzir(estado):
    """Produza as amostras numeradas de zero até total menos um.

    Parâmetros:
        estado (Estado): buffer e variáveis compartilhadas desta execução.
    Retorno:
        None. Atualiza buffer, índice de escrita e quantidade produzida.
    Funcionamento:
        V1 espera ocupada e separa leitura/escrita do contador com sleep(0).
        V2 adquire vazio antes de mutex. V3 adquire mutex antes de vazio.
        As versões sincronizadas publicam cheio depois de liberar mutex.
    """
    for amostra in range(estado.total):
        if estado.parar.is_set():
            estado.produtor_estado = "encerrado pelo observador"
            return

        if estado.versao == 1:
            estado.produtor_estado = "espera ocupada por espaço"
            while estado.ocupadas >= N and not estado.parar.is_set():
                pass
            if estado.parar.is_set():
                estado.produtor_estado = "encerrado pelo observador"
                return
        elif estado.versao == 2:
            estado.produtor_estado = "aguarda vazio"
            estado.vazio.acquire()
            estado.produtor_estado = "tem vaga; aguarda mutex"
            estado.mutex.acquire()
        else:
            # ÚNICA mudança de algoritmo da versão 2 para a versão 3.
            estado.produtor_estado = "aguarda mutex"
            estado.mutex.acquire()
            estado.produtor_estado = "segura mutex; aguarda vazio"
            estado.vazio.acquire()

        estado.produtor_estado = "atualiza buffer e contador"
        estado.buffer[estado.escrita] = amostra
        estado.escrita = (estado.escrita + 1) % N
        if estado.versao == 1:
            ocupadas_lidas = estado.ocupadas
            time.sleep(0)  # Troca de contexto entre ler e escrever: corrida.
            estado.ocupadas = ocupadas_lidas + 1
        else:
            estado.ocupadas += 1
        estado.produzidas += 1

        if estado.versao in (2, 3):
            estado.mutex.release()
            estado.cheio.release()

    estado.produtor_terminou = True
    estado.produtor_estado = "concluiu a produção"


def consumir(estado):
    """Leia até total entradas do buffer e registre a sequência observada.

    Parâmetros:
        estado (Estado): buffer e variáveis compartilhadas desta execução.
    Retorno:
        None. Atualiza a sequência consumida e o instante do último consumo.
    Funcionamento:
        A pausa inicial igual em todas as versões exercita o caso buffer cheio.
        V1 espera ocupada e usa sleep(0) entre ler e escrever o contador.
        V2/V3 adquirem cheio, depois mutex, e liberam mutex, depois vazio.
        As células não são apagadas: como em um buffer circular convencional,
        são os índices e a ocupação que determinam quais posições são válidas.
    """
    estado.consumidor_estado = "pausa inicial controlada"
    time.sleep(estado.atraso_consumidor)
    while len(estado.consumidas) < estado.total:
        if estado.parar.is_set():
            estado.consumidor_estado = "encerrado pelo observador"
            return

        if estado.versao == 1:
            estado.consumidor_estado = "espera ocupada por amostra"
            while estado.ocupadas <= 0 and not estado.parar.is_set():
                pass
            if estado.parar.is_set():
                estado.consumidor_estado = "encerrado pelo observador"
                return
        else:
            estado.consumidor_estado = "aguarda cheio"
            estado.cheio.acquire()
            estado.consumidor_estado = "tem item; aguarda mutex"
            estado.mutex.acquire()

        estado.consumidor_estado = "lê buffer e atualiza contador"
        amostra = estado.buffer[estado.leitura]
        estado.leitura = (estado.leitura + 1) % N
        if estado.versao == 1:
            ocupadas_lidas = estado.ocupadas
            time.sleep(0)  # Atualização perdida também pode partir do leitor.
            estado.ocupadas = ocupadas_lidas - 1
        else:
            estado.ocupadas -= 1
        estado.consumidas.append(amostra)
        estado.ultimo_consumo = time.monotonic()

        if estado.versao in (2, 3):
            estado.mutex.release()
            estado.vazio.release()

    estado.consumidor_terminou = True
    estado.consumidor_estado = "concluiu as leituras planejadas"


def executar_thread(estado, tarefa):
    """Capture erros de uma thread para que o processo principal os registre.

    Parâmetros:
        estado (Estado): estado ao qual pertence a thread.
        tarefa (callable): função produzir ou consumir, que recebe estado.
    Retorno:
        None. Um erro inesperado é adicionado a estado.erros.
    Funcionamento:
        Apenas erros de execução acionam parar aqui. Esperas em semáforos não
        são interrompidas, liberadas nem transformadas em sucesso artificial.
    """
    try:
        tarefa(estado)
    except Exception as erro:
        estado.erros.append(f"{tarefa.__name__}: {type(erro).__name__}: {erro}")
        estado.parar.set()


def resumir(estado, duracao, travou, motivo, estados_no_fim, threads):
    """Calcule métricas a partir das leituras realmente registradas.

    Parâmetros:
        estado (Estado): execução observada após o encerramento da coleta.
        duracao (float): tempo de observação, em segundos, sem os joins finais.
        travou (bool): True quando o watchdog detectou um segundo sem consumo.
        motivo (str): condição que encerrou a observação.
        estados_no_fim (dict): etapas das threads no instante do encerramento.
        threads (tuple): threads produtora e consumidora, para consultar vida.
    Retorno:
        dict: resultado, parâmetros, ambiente e sequência bruta de consumo.
    Funcionamento:
        Consumidas inclui repetições válidas. Perdidas significa IDs ausentes
        do universo planejado 0..total-1, inclusive os ainda não produzidos.
        Campos separados distinguem não produzidas e produzidas não recebidas.
    """
    valores = list(estado.consumidas)
    validos = [valor for valor in valores if isinstance(valor, int) and 0 <= valor < estado.total]
    frequencias = Counter(validos)
    recebidas = set(frequencias)
    faltantes = [valor for valor in range(estado.total) if valor not in recebidas]
    produzidas_nao_recebidas = sum(
        valor not in recebidas for valor in range(estado.produzidas)
    )
    return {
        "descricao": "A4: execução real de buffer circular; métricas calculadas das leituras",
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "versao": estado.versao,
        "parametros": PARAMETROS,
        "planejadas": estado.total,
        "produzidas": estado.produzidas,
        "leituras_buffer": len(valores),
        "consumidas": len(validos),
        "distintas": len(recebidas),
        "perdidas": len(faltantes),
        "duplicadas": len(validos) - len(recebidas),
        "invalidas": len(valores) - len(validos),
        "nao_produzidas": estado.total - estado.produzidas,
        "produzidas_nao_recebidas": produzidas_nao_recebidas,
        "travou": travou,
        "motivo": motivo,
        "duracao_s": round(duracao, 6),
        "limite_inatividade_s": LIMITE_INATIVIDADE_S,
        "atraso_inicial_consumidor_s": estado.atraso_consumidor,
        "fifo_exato": valores == list(range(estado.total)),
        "ocupadas_final": estado.ocupadas,
        "buffer_final": list(estado.buffer),
        "etapas_ao_encerrar": estados_no_fim,
        "threads_ainda_bloqueadas": [thread.name for thread in threads if thread.is_alive()],
        "primeiras_faltantes": faltantes[:12],
        "primeiras_duplicatas": [valor for valor, quantidade in frequencias.items() if quantidade > 1][:12],
        "erros": list(estado.erros),
        "ambiente": {
            "python": platform.python_version(),
            "implementacao": platform.python_implementation(),
            "sistema": platform.platform(),
            "arquitetura": platform.machine(),
        },
        "sequencia_consumida": valores,
    }


def executar_experimento(versao, total=TOTAL_AMOSTRAS, atraso_consumidor=ATRASO_INICIAL_CONSUMIDOR_S):
    """Execute uma versão com duas threads e watchdog externo ao buffer.

    Parâmetros:
        versao (int): 1 (corrida), 2 (correta) ou 3 (ordem invertida).
        total (int): número positivo de amostras; padrão exigido: 20.000.
        atraso_consumidor (float): pausa inicial não negativa, em segundos.
    Retorno:
        dict: resultado produzido por resumir, incluindo a sequência completa.
    Funcionamento:
        Inicia produtor e consumidor; verifica progresso a cada cerca de 5 ms.
        Sem consumo durante 1 s, registra travamento. As threads são daemon:
        se houver deadlock, permanecem bloqueadas até o subprocesso terminar.
        O observador nunca libera os semáforos para esconder esse bloqueio.
        V1 recebe sinal de parada e sai das suas esperas ocupadas.
    """
    if versao not in (1, 2, 3) or total < 1 or atraso_consumidor < 0:
        raise ValueError("Versão, total ou atraso inicial inválido.")
    estado = Estado(versao, total, atraso_consumidor)
    produtor = threading.Thread(
        target=executar_thread, args=(estado, produzir), name="produtor", daemon=True
    )
    consumidor = threading.Thread(
        target=executar_thread, args=(estado, consumir), name="consumidor", daemon=True
    )
    inicio = time.monotonic()
    estado.ultimo_consumo = inicio
    produtor.start()
    consumidor.start()
    travou = False
    motivo = "consumidor concluiu as leituras planejadas; conferir integridade"
    while not estado.consumidor_terminou:
        if estado.erros:
            motivo = "erro inesperado de execução"
            break
        if time.monotonic() - estado.ultimo_consumo >= LIMITE_INATIVIDADE_S:
            travou = True
            motivo = "watchdog: consumidor ficou 1 s sem receber nova amostra"
            break
        time.sleep(0.005)
    duracao = time.monotonic() - inicio
    estados_no_fim = {
        "produtor": estado.produtor_estado,
        "consumidor": estado.consumidor_estado,
    }
    estado.parar.set()
    produtor.join(timeout=0.1)
    consumidor.join(timeout=0.1)
    return resumir(estado, duracao, travou, motivo, estados_no_fim, (produtor, consumidor))


def imprimir_resultado(resultado):
    """Imprima um relatório compacto e fiel aos dados do experimento.

    Parâmetros:
        resultado (dict): retorno de executar_experimento.
    Retorno:
        None. Escreve somente o resumo em stdout, sem a sequência completa.
    Funcionamento:
        Explicita as definições das métricas e as etapas observadas das threads.
        O relatório serve de log textual e de fonte para os prints da entrega.
    """
    p = resultado["parametros"]
    print(f"A4 | Versão {resultado['versao']} | Buffer circular")
    print(f"Autor: {p['nome']} | D1={p['D1']} | D2={p['D2']} | N={p['N']}")
    print(f"Python {resultado['ambiente']['python']} | {resultado['ambiente']['implementacao']}")
    print(f"Amostras planejadas: {resultado['planejadas']} | Pausa inicial: {resultado['atraso_inicial_consumidor_s']:.3f} s")
    print(f"Produzidas: {resultado['produzidas']}")
    print(f"Consumidas: {resultado['consumidas']} | Distintas: {resultado['distintas']}")
    print(f"Perdidas: {resultado['perdidas']} | Duplicadas: {resultado['duplicadas']} | Inválidas: {resultado['invalidas']}")
    print(f"Não produzidas: {resultado['nao_produzidas']} | Produzidas não recebidas: {resultado['produzidas_nao_recebidas']}")
    print(f"Travou: {'SIM' if resultado['travou'] else 'NÃO'} | FIFO exato: {'SIM' if resultado['fifo_exato'] else 'NÃO'}")
    print(f"Tempo observado: {resultado['duracao_s']:.3f} s | Ocupadas ao final: {resultado['ocupadas_final']}")
    print(f"Motivo: {resultado['motivo']}")
    print(f"Produtor: {resultado['etapas_ao_encerrar']['produtor']}")
    print(f"Consumidor: {resultado['etapas_ao_encerrar']['consumidor']}")
    print(f"Threads ainda bloqueadas: {', '.join(resultado['threads_ainda_bloqueadas']) or 'nenhuma'}")
    print(f"Primeiras 12 leituras: {resultado['sequencia_consumida'][:12]}")
    print(f"Primeiros IDs faltantes: {resultado['primeiras_faltantes']}")
    print(f"Primeiros IDs duplicados: {resultado['primeiras_duplicatas']}")
    print("Perdidas = IDs ausentes entre 0 e planejadas-1; inclui não produzidas.")
    print("Consumidas inclui repetições válidas; duplicadas = consumidas - distintas.")
    if resultado["erros"]:
        print("Erros: " + "; ".join(resultado["erros"]))


def executar_interface(versao):
    """Processe os argumentos do script e execute uma única experiência.

    Parâmetros:
        versao (int): versão fixa informada pelo respectivo script de entrada.
    Retorno:
        int: código 0 para experimento concluído; 1 para erro inesperado.
    Funcionamento:
        Sem argumentos executa 20.000 amostras com N individual. --json salva
        também os dados brutos. Travar em V1/V3 é resultado, não erro do script.
        --amostras e --atraso-consumidor permitem experiências adicionais;
        as nove execuções da entrega usam sempre os valores padrão.
    """
    parser = argparse.ArgumentParser(description=f"A4, versão {versao}: buffer circular de N={N} posições.")
    parser.add_argument("--json", type=Path, help="Arquivo opcional para métricas e sequência de consumo.")
    parser.add_argument("--amostras", type=int, default=TOTAL_AMOSTRAS, help="Padrão da entrega: 20000.")
    parser.add_argument("--atraso-consumidor", type=float, default=ATRASO_INICIAL_CONSUMIDOR_S, help="Pausa inicial em segundos; padrão: 0.020.")
    argumentos = parser.parse_args()
    if argumentos.amostras < 1 or argumentos.atraso_consumidor < 0:
        parser.error("--amostras deve ser positivo e --atraso-consumidor não pode ser negativo.")
    resultado = executar_experimento(versao, argumentos.amostras, argumentos.atraso_consumidor)
    imprimir_resultado(resultado)
    if argumentos.json is not None:
        argumentos.json.parent.mkdir(parents=True, exist_ok=True)
        argumentos.json.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Dados brutos salvos em: {argumentos.json}")
    return 1 if resultado["erros"] else 0
