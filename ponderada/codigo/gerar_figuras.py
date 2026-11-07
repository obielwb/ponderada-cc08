"""Gere os cinco diagramas didáticos da ponderada CC08.

Autor: Gabriel Willian Bartmanovicz.
Dependência opcional: Pillow; a A4 usa somente a biblioteca padrão.
As capturas reais das caches e dos experimentos são preservadas.
Este auxiliar não cria nem sobrescreve evidências de execução.
"""

from functools import lru_cache
import math
import os
from pathlib import Path
import sys

try:
    from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
except ImportError as erro:
    raise SystemExit(
        "Geração opcional de figuras requer Pillow: python3 -m pip install Pillow"
    ) from erro


PASTA_CODIGO = Path(__file__).resolve().parent
PASTA_IMG = PASTA_CODIGO.parent / "img"
PASTA_RESULTADOS = PASTA_CODIGO / "resultados"
LARGURA = 1880
TEXTO = "#16283d"
SECUNDARIO = "#526278"
AZUL = "#235da8"
AZUL_CLARO = "#edf4fc"
BORDA = "#d9e1eb"
FUNDO = "#ffffff"


@lru_cache(maxsize=None)
def fonte(tamanho, negrito=False, mono=False):
    """Localize uma fonte legível, com alternativas para Linux, macOS e Windows.

    Parâmetros:
        tamanho (int): tamanho da fonte em pixels.
        negrito (bool): solicita peso forte para títulos.
        mono (bool): solicita largura fixa para código e registros.
    Retorno:
        PIL.ImageFont.FreeTypeFont: fonte encontrada e carregada.
    Funcionamento:
        Primeiro consulta as variáveis PONDERADA_FONTE, PONDERADA_FONTE_MONO
        ou PONDERADA_FONTE_NEGRITO. Depois tenta fontes comuns dos sistemas.
        Se nenhuma existir, explica como indicar uma fonte explicitamente.
    """
    if mono:
        variavel = "PONDERADA_FONTE_MONO"
        candidatos = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/Supplemental/Courier New.ttf",
            "C:/Windows/Fonts/consola.ttf",
            "DejaVuSansMono.ttf",
        ]
    elif negrito:
        variavel = "PONDERADA_FONTE_NEGRITO"
        candidatos = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "DejaVuSans-Bold.ttf",
        ]
    else:
        variavel = "PONDERADA_FONTE"
        candidatos = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "DejaVuSans.ttf",
        ]
    caminho_personalizado = os.environ.get(variavel)
    if caminho_personalizado:
        candidatos.insert(0, caminho_personalizado)
    for candidato in candidatos:
        try:
            return ImageFont.truetype(candidato, tamanho)
        except OSError:
            continue
    raise RuntimeError(
        f"Fonte não encontrada. Defina {variavel} com o caminho de um TTF/OTF."
    )


def tela(titulo, subtitulo, altura):
    """Crie a base branca de uma figura com título e subtítulo.

    Parâmetros:
        titulo (str): identificação principal da figura.
        subtitulo (str): explicação curta, em uma linha.
        altura (int): altura total em pixels.
    Retorno:
        tuple: imagem PIL e objeto ImageDraw para desenhar sobre ela.
    Funcionamento:
        Usa largura constante de 1880 pixels, margens de 64 pixels e uma
        linha azul de destaque; não imita janelas de terminal ou capturas.
    """
    imagem = Image.new("RGB", (LARGURA, altura), FUNDO)
    desenho = ImageDraw.Draw(imagem)
    desenho.rectangle((0, 0, LARGURA, 10), fill=AZUL)
    desenho.text((64, 46), titulo, font=fonte(40, negrito=True), fill=TEXTO)
    desenho.text((64, 109), subtitulo, font=fonte(25), fill=SECUNDARIO)
    return imagem, desenho


def texto_central(desenho, centro, texto, tamanho=26, cor=TEXTO, negrito=False, mono=False):
    """Desenhe texto centralizado, admitindo múltiplas linhas explícitas.

    Parâmetros:
        desenho (ImageDraw): superfície de desenho da imagem.
        centro (tuple): coordenadas x e y do centro do bloco.
        texto (str): conteúdo a desenhar; aceita caracteres de nova linha.
        tamanho (int): tamanho da fonte em pixels.
        cor (str): cor do texto em hexadecimal.
        negrito (bool): solicita uma fonte de peso forte.
        mono (bool): solicita uma fonte monoespaçada.
    Retorno:
        None: modifica a superfície recebida.
    Funcionamento:
        Mede o bloco completo e ajusta sua posição para centralizar tanto
        a largura como a altura, incluindo os deslocamentos da fonte.
    """
    f = fonte(tamanho, negrito=negrito, mono=mono)
    limites = desenho.multiline_textbbox((0, 0), texto, font=f, spacing=9, align="center")
    x = centro[0] - (limites[2] - limites[0]) / 2 - limites[0]
    y = centro[1] - (limites[3] - limites[1]) / 2 - limites[1]
    desenho.multiline_text((x, y), texto, font=f, fill=cor, spacing=9, align="center")


def salvar(imagem, nome, descricao):
    """Salve uma figura PNG com uma descrição da sua origem.

    Parâmetros:
        imagem (Image.Image): figura já montada.
        nome (str): nome do PNG dentro de ponderada/img.
        descricao (str): origem e significado da figura.
    Retorno:
        pathlib.Path: caminho absoluto do arquivo salvo.
    Funcionamento:
        Cria a pasta de destino quando necessário, grava o PNG sem perdas
        e inclui metadados textuais que distinguem diagramas e registros.
    """
    PASTA_IMG.mkdir(parents=True, exist_ok=True)
    destino = PASTA_IMG / nome
    metadados = PngImagePlugin.PngInfo()
    metadados.add_text("Description", descricao)
    metadados.add_text("Author", "Gabriel Willian Bartmanovicz")
    imagem.save(destino, pnginfo=metadados)
    return destino


def gerar_pipeline(nome, titulo, ciclos, bolhas, linhas, observacao):
    """Desenhe um diagrama ciclo a ciclo a partir de estágios explícitos.

    Parâmetros:
        nome (str): nome do arquivo PNG de saída.
        titulo (str): título da configuração de pipeline.
        ciclos (int): ciclo do último WB da sequência.
        bolhas (int): quantidade total de ciclos perdidos por stalls.
        linhas (list): pares de rótulo e dict que associa ciclo a estágio.
        observacao (str): nota específica sobre as dependências da figura.
    Retorno:
        pathlib.Path: caminho da imagem PNG produzida.
    Funcionamento:
        Desenha uma tabela com uma linha por instrução; IF/ID repetidos
        mostram retenção por hazards. WB* identifica o quinto estágio
        neutro do store, que não escreve no banco de registradores.
    """
    subtitulo = f"7 instruções  •  {bolhas} bolhas  •  {ciclos} ciclos do primeiro IF ao último WB"
    imagem, desenho = tela(titulo, subtitulo, 1030)
    x0, y0, rotulo, linha_h, cabecalho_h = 64, 195, 305, 74, 56
    coluna_w = (LARGURA - 2 * x0 - rotulo) / ciclos
    cores = {
        "IF": "#e5effc",
        "ID": "#fff0ce",
        "EX": "#dcefee",
        "MEM": "#ebe6f6",
        "WB": "#e8edf3",
        "WB*": "#e8edf3",
    }
    desenho.rectangle((x0, y0, LARGURA - x0, y0 + cabecalho_h), fill=AZUL_CLARO)
    desenho.text((x0 + 18, y0 + 14), "Instrução original", font=fonte(24, negrito=True), fill=TEXTO)
    for ciclo in range(1, ciclos + 1):
        xc = x0 + rotulo + (ciclo - 0.5) * coluna_w
        texto_central(desenho, (xc, y0 + cabecalho_h / 2), str(ciclo), 24, negrito=True)
    for indice, (rotulo_instrucao, estagios) in enumerate(linhas):
        y = y0 + cabecalho_h + indice * linha_h
        fundo_linha = "#ffffff" if indice % 2 == 0 else "#f8fafc"
        desenho.rectangle((x0, y, LARGURA - x0, y + linha_h), fill=fundo_linha)
        desenho.text((x0 + 18, y + 24), rotulo_instrucao, font=fonte(24, mono=True), fill=TEXTO)
        for ciclo in range(1, ciclos + 1):
            x = x0 + rotulo + (ciclo - 1) * coluna_w
            if ciclo in estagios:
                estagio = estagios[ciclo]
                desenho.rounded_rectangle(
                    (x + 5, y + 10, x + coluna_w - 5, y + linha_h - 10),
                    radius=8,
                    fill=cores[estagio],
                )
                texto_central(desenho, (x + coluna_w / 2, y + linha_h / 2), estagio, 24, negrito=True)
            else:
                texto_central(desenho, (x + coluna_w / 2, y + linha_h / 2), "·", 22, cor="#bac6d4")
        desenho.line((x0, y + linha_h, LARGURA - x0, y + linha_h), fill=BORDA, width=1)
    desenho.rounded_rectangle((64, 814, 1816, 982), radius=15, fill="#f3f6fa")
    notas = [
        "IF/ID repetidos: instrução retida durante o stall. WB*: passagem sem escrita do sw.",
        "Banco de registradores: escrita na 1ª metade; leitura na 2ª metade do mesmo ciclo.",
        observacao,
    ]
    for i, nota in enumerate(notas):
        desenho.text((86, 836 + 43 * i), nota, font=fonte(24), fill=SECUNDARIO)
    return salvar(imagem, nome, titulo + "; diagrama didático, não medição de hardware.")


def diagramas_pipeline():
    """Produza os três diagramas de pipeline da questão A2.

    Parâmetros:
        Nenhum; as sequências correspondem ao trecho RISC-V do enunciado.
    Retorno:
        list[pathlib.Path]: caminhos dos três PNGs gerados.
    Funcionamento:
        Define cada estágio por ciclo, sem simular resultados. Usa
        forwarding completo, inclusive para o dado gravado por sw, e
        separação dos acessos IF/MEM para não haver hazard estrutural.
    """
    sem = [
        ("I1  lw   x5", {1: "IF", 2: "ID", 3: "EX", 4: "MEM", 5: "WB"}),
        ("I2  add  x6", {2: "IF", 3: "ID", 4: "ID", 5: "ID", 6: "EX", 7: "MEM", 8: "WB"}),
        ("I3  lw   x7", {3: "IF", 4: "IF", 5: "IF", 6: "ID", 7: "EX", 8: "MEM", 9: "WB"}),
        ("I4  sub  x6", {6: "IF", 7: "ID", 8: "ID", 9: "ID", 10: "EX", 11: "MEM", 12: "WB"}),
        ("I5  sw   x6", {7: "IF", 8: "IF", 9: "IF", 10: "ID", 11: "ID", 12: "ID", 13: "EX", 14: "MEM", 15: "WB*"}),
        ("I6  addi x10", {10: "IF", 11: "IF", 12: "IF", 13: "ID", 14: "EX", 15: "MEM", 16: "WB"}),
        ("I7  addi x11", {13: "IF", 14: "ID", 15: "EX", 16: "MEM", 17: "WB"}),
    ]
    com = [
        ("I1  lw   x5", {1: "IF", 2: "ID", 3: "EX", 4: "MEM", 5: "WB"}),
        ("I2  add  x6", {2: "IF", 3: "ID", 4: "ID", 5: "EX", 6: "MEM", 7: "WB"}),
        ("I3  lw   x7", {3: "IF", 4: "IF", 5: "ID", 6: "EX", 7: "MEM", 8: "WB"}),
        ("I4  sub  x6", {5: "IF", 6: "ID", 7: "ID", 8: "EX", 9: "MEM", 10: "WB"}),
        ("I5  sw   x6", {6: "IF", 7: "IF", 8: "ID", 9: "EX", 10: "MEM", 11: "WB*"}),
        ("I6  addi x10", {8: "IF", 9: "ID", 10: "EX", 11: "MEM", 12: "WB"}),
        ("I7  addi x11", {9: "IF", 10: "ID", 11: "EX", 12: "MEM", 13: "WB"}),
    ]
    ordem = [(1, "lw   x5"), (3, "lw   x7"), (2, "add  x6"), (4, "sub  x6"), (5, "sw   x6"), (6, "addi x10"), (7, "addi x11")]
    reordenado = []
    for posicao, (numero, operacao) in enumerate(ordem, start=1):
        estagios = {}
        for deslocamento, estagio in enumerate(("IF", "ID", "EX", "MEM", "WB*" if numero == 5 else "WB")):
            estagios[posicao + deslocamento] = estagio
        reordenado.append((f"I{numero}  {operacao}", estagios))
    return [
        gerar_pipeline("pipeline_sem_forwarding.png", "A2 | Pipeline sem forwarding", 17, 6, sem,
                       "I2 lê x5 no ciclo 5; I4 lê x6/x7 no 9; I5 lê x6 no 12."),
        gerar_pipeline("pipeline_com_forwarding.png", "A2 | Pipeline com forwarding", 13, 2, com,
                       "Load-use: I1 → I2 e I3 → I4. Inclui forwarding do dado do sw."),
        gerar_pipeline("pipeline_reordenado.png", "A2 | Pipeline reordenado", 11, 0, reordenado,
                       "Ordem 1, 3, 2, 4, 5, 6, 7. Os dois loads ganham uma instrução de intervalo."),
    ]


def seta(desenho, pontos, cor=AZUL, largura=5, tracejada=False):
    """Desenhe uma seta, contínua ou tracejada, ao longo de uma polilinha.

    Parâmetros:
        desenho (ImageDraw): superfície a modificar.
        pontos (list[tuple]): vértices em ordem da origem para o destino.
        cor (str): cor da linha e da ponta.
        largura (int): espessura da linha em pixels.
        tracejada (bool): usa traços separados quando True.
    Retorno:
        None: desenha diretamente sobre a figura.
    Funcionamento:
        Traça cada segmento e acrescenta um triângulo na direção do último
        segmento, mantendo visível a orientação das relações.
    """
    for inicio, fim in zip(pontos, pontos[1:]):
        dx, dy = fim[0] - inicio[0], fim[1] - inicio[1]
        distancia = math.hypot(dx, dy)
        if tracejada and distancia:
            passo = 0.0
            while passo < distancia:
                ate = min(passo + 18, distancia)
                a = (inicio[0] + dx * passo / distancia, inicio[1] + dy * passo / distancia)
                b = (inicio[0] + dx * ate / distancia, inicio[1] + dy * ate / distancia)
                desenho.line((a, b), fill=cor, width=largura)
                passo += 29
        else:
            desenho.line((inicio, fim), fill=cor, width=largura)
    anterior, fim = pontos[-2], pontos[-1]
    angulo = math.atan2(fim[1] - anterior[1], fim[0] - anterior[0])
    comprimento, meia_largura = 19, 9
    base = (fim[0] - comprimento * math.cos(angulo), fim[1] - comprimento * math.sin(angulo))
    a = (base[0] + meia_largura * math.sin(angulo), base[1] - meia_largura * math.cos(angulo))
    b = (base[0] - meia_largura * math.sin(angulo), base[1] + meia_largura * math.cos(angulo))
    desenho.polygon((fim, a, b), fill=cor)


def gerar_estados():
    """Gere o diagrama de cinco estados de um processo da questão A3.

    Parâmetros:
        Nenhum; usa os estados clássicos Novo, Pronto, Executando,
        Bloqueado e Terminado.
    Retorno:
        pathlib.Path: caminho de estados_processo.png.
    Funcionamento:
        Representa admissão, despacho, preempção, espera, conclusão de
        evento e saída. A nota explica a espera periódica do sensor.
    """
    imagem, desenho = tela("A3 | Estados de um processo", "A espera por evento ou temporizador bloqueia a thread e libera a CPU.", 970)
    caixas = {
        "Novo": (100, 310, 340, 430),
        "Pronto": (520, 310, 790, 430),
        "Executando": (1035, 310, 1335, 430),
        "Terminado": (1540, 310, 1805, 430),
        "Bloqueado": (790, 650, 1090, 770),
    }
    seta(desenho, [(340, 370), (520, 370)])
    seta(desenho, [(790, 370), (1035, 370)])
    seta(desenho, [(1335, 370), (1540, 370)])
    seta(desenho, [(1185, 310), (1185, 215), (655, 215), (655, 310)])
    seta(desenho, [(1170, 430), (1030, 650)])
    seta(desenho, [(830, 650), (665, 430)])
    texto_central(desenho, (429, 334), "admissão", 24)
    texto_central(desenho, (912, 334), "despacho", 24)
    texto_central(desenho, (1438, 334), "saída", 24)
    texto_central(desenho, (920, 183), "preempção / fim da fatia", 25)
    texto_central(desenho, (1264, 548), "espera por E/S\nou evento", 25)
    texto_central(desenho, (593, 548), "E/S ou evento\nconcluído", 25)
    for nome, retangulo in caixas.items():
        cor = AZUL_CLARO if nome != "Bloqueado" else "#fff3d9"
        desenho.rounded_rectangle(retangulo, radius=22, fill=cor, outline=BORDA, width=3)
        centro = ((retangulo[0] + retangulo[2]) / 2, (retangulo[1] + retangulo[3]) / 2)
        texto_central(desenho, centro, nome, 30, negrito=True)
    desenho.rounded_rectangle((64, 828, 1816, 930), radius=14, fill="#f3f6fa")
    desenho.text((87, 849), "Sensor: bloqueada entre ativações de 10 ms, quando aguarda temporizador ou E/S.", font=fonte(25), fill=SECUNDARIO)
    desenho.text((87, 888), "Depois do evento, passa a Pronto e aguarda o escalonador; não retorna diretamente a Executando.", font=fonte(24), fill=SECUNDARIO)
    return salvar(imagem, "estados_processo.png", "Diagrama didático dos cinco estados clássicos de um processo.")


def fronteira(no, destino):
    """Calcule a interseção de uma aresta com a borda de um nó.

    Parâmetros:
        no (dict): centro, tipo e dimensão do nó de origem.
        destino (tuple): coordenadas do centro do outro nó.
    Retorno:
        tuple[float, float]: ponto de saída na borda do círculo ou retângulo.
    Funcionamento:
        Projeta a direção entre os centros até o raio do círculo ou a
        primeira face do retângulo, evitando setas sobre os rótulos.
    """
    x, y = no["centro"]
    dx, dy = destino[0] - x, destino[1] - y
    if no["tipo"] == "thread":
        escala = no["raio"] / math.hypot(dx, dy)
    else:
        proporcoes = []
        if dx:
            proporcoes.append(no["largura"] / (2 * abs(dx)))
        if dy:
            proporcoes.append(no["altura"] / (2 * abs(dy)))
        escala = min(proporcoes)
    return x + dx * escala, y + dy * escala


def gerar_deadlock():
    """Gere o grafo de alocação e espera do deadlock da questão A5.

    Parâmetros:
        Nenhum; utiliza as três threads e os três recursos do enunciado.
    Retorno:
        pathlib.Path: caminho de grafo_deadlock.png.
    Funcionamento:
        Desenha threads como círculos e recursos de uma instância como
        retângulos. Arestas azuis recurso→thread indicam alocação; arestas
        tracejadas thread→recurso indicam pedido ainda não atendido.
    """
    imagem, desenho = tela("A5 | Grafo no instante do deadlock", "Cada recurso tem uma instância. As três threads mantêm um recurso e esperam pelo próximo.", 1230)
    nos = {
        "i2c": {"tipo": "recurso", "centro": (430, 410), "largura": 280, "altura": 140, "rotulo": "I2C"},
        "sensor": {"tipo": "thread", "centro": (940, 285), "raio": 116, "rotulo": "thread_sensor"},
        "log": {"tipo": "recurso", "centro": (1450, 410), "largura": 280, "altura": 140, "rotulo": "Arquivo de log"},
        "tlog": {"tipo": "thread", "centro": (1450, 830), "raio": 116, "rotulo": "thread_log"},
        "ble": {"tipo": "recurso", "centro": (940, 940), "largura": 280, "altura": 140, "rotulo": "Rádio BLE"},
        "config": {"tipo": "thread", "centro": (430, 830), "raio": 116, "rotulo": "thread_config"},
    }
    arestas = [
        ("i2c", "sensor", False, (650, 298), "alocado"),
        ("sensor", "log", True, (1232, 298), "solicita"),
        ("log", "tlog", False, (1564, 595), "alocado"),
        ("tlog", "ble", True, (1229, 960), "solicita"),
        ("ble", "config", False, (648, 960), "alocado"),
        ("config", "i2c", True, (318, 595), "solicita"),
    ]
    for origem, destino, pedido, centro_rotulo, rotulo in arestas:
        a = fronteira(nos[origem], nos[destino]["centro"])
        b = fronteira(nos[destino], nos[origem]["centro"])
        seta(desenho, [a, b], cor=SECUNDARIO if pedido else AZUL, tracejada=pedido)
        texto_central(desenho, centro_rotulo, rotulo, 25, cor=SECUNDARIO if pedido else AZUL)
    for no in nos.values():
        x, y = no["centro"]
        if no["tipo"] == "thread":
            r = no["raio"]
            desenho.ellipse((x - r, y - r, x + r, y + r), fill=AZUL_CLARO, outline=AZUL, width=3)
            texto_central(desenho, (x, y), no["rotulo"], 25, mono=True)
        else:
            w, h = no["largura"] / 2, no["altura"] / 2
            desenho.rectangle((x - w, y - h, x + w, y + h), fill="#f6f8fb", outline=SECUNDARIO, width=3)
            texto_central(desenho, (x, y - 22), no["rotulo"], 28, negrito=True)
            desenho.ellipse((x - 67, y + 22, x - 55, y + 34), fill=AZUL)
            texto_central(desenho, (x + 18, y + 29), "1 instância", 23, cor=SECUNDARIO)
    desenho.rounded_rectangle((64, 1082, 1816, 1190), radius=14, fill="#f3f6fa")
    seta(desenho, [(91, 1114), (199, 1114)], cor=AZUL)
    desenho.text((221, 1098), "Recurso → thread: alocação", font=fonte(24), fill=SECUNDARIO)
    seta(desenho, [(932, 1114), (1040, 1114)], cor=SECUNDARIO, tracejada=True)
    desenho.text((1062, 1098), "Thread → recurso: pedido", font=fonte(24), fill=SECUNDARIO)
    desenho.text((90, 1148), "Ciclo de espera: sensor → log → thread_log → BLE → config → I2C → sensor.", font=fonte(24), fill=SECUNDARIO)
    return salvar(imagem, "grafo_deadlock.png", "Grafo de alocação de recursos da A5; cada recurso tem uma única instância.")


def main():
    """Gere os diagramas de pipeline, estados de processo e deadlock.

    Parâmetros:
        Nenhum. Fontes opcionais são indicadas pelas variáveis PONDERADA_FONTE.
    Retorno:
        int: zero após gravar os cinco PNGs didáticos em ponderada/img.
    Funcionamento:
        Desenha somente figuras conceituais; preserva todos os prints reais.
    """
    gerados = diagramas_pipeline()
    gerados.extend((gerar_estados(), gerar_deadlock()))
    for caminho in gerados:
        print(caminho.relative_to(PASTA_CODIGO.parent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
