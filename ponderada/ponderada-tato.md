Gabriel Willian Bartmanovicz — D1 = 7; D2 = 6; N = 4.

# Ponderada Computação CC08: do pipeline ao deadlock

## Parâmetros individuais e critérios

Meu nome completo tem 26 letras: `Gabriel = 7`, `Willian = 7` e `Bartmanovicz = 12`. Os parâmetros ficam:

$$
D1 = 7,\qquad D2 = (7+7+12)\bmod 10 = 6
$$

$$
IC = 100.000+20.000\times6 = 220.000\ \text{instruções/amostra}
$$

$$
m = 3\%+0,5\%\times7 = 6,5\% = 0,065
$$

$$
N = 3+(6\bmod5) = 4\ \text{posições}
$$

A pulseira recebe uma amostra a cada `1/100 Hz = 10 ms`, mas precisa processá-la em **até 5 ms**. Vou usar esse prazo nas comparações, com os valores de hardware e custo do enunciado.

# Parte A — O problema técnico

## A1. Arquitetura e memória

### A1.1. Plataforma H

Para calcular o tempo, multiplico as instruções pelo CPI e divido pelo clock:

$$
T_H = \frac{IC\times CPI}{f}
=\frac{220.000\times1,5}{48.000.000}
=0,006875\ s=\boxed{6,875\ ms}
$$

São `330.000 ciclos` por amostra. **A H sem DSP não atende:** passa do prazo em `6,875 − 5 = 1,875 ms`. Ela termina antes da próxima amostra, mas isso ainda é tarde para o limite de 5 ms.

### A1.2. Plataforma V: AMAT, CPI e atraso do Linux

Trato os **120 ciclos como penalidade adicional da falta**, seguindo a fórmula de CPI do enunciado. No AMAT, somo o tempo de acerto à penalidade multiplicada pela taxa de falta [R1]:

$$
AMAT = T_{acerto}+m\times P_{falta}
=1+0,065\times120
=\boxed{8,8\ ciclos/acesso}
$$

Como `1 ciclo = 1/(1,2 × 10⁹) s = 0,833333 ns`, o AMAT também equivale a:

$$
AMAT=8,8\times0,833333\approx\boxed{7,333333\ ns}
$$

O CPI básico já considera os acertos. Acrescento o custo das faltas:

$$
CPI_{efetivo}=1,0+1,3\times0,065\times120
=1+10,14=\boxed{11,14}
$$

$$
T_V=\frac{220.000\times11,14}{1.200.000.000}
=\frac{2.450.800}{1.200.000.000}\ s
\approx\boxed{2,042333\ ms}
$$

Somando o atraso máximo do sistema operacional informado:

$$
T_{V,\ pior\ caso\ do\ modelo}=2,042333+3
\approx\boxed{5,042333\ ms}
$$

**A V atende na média, mas ultrapassa o prazo no pior caso pedido em cerca de `0,042333 ms`.** A diferença é pequena, porém o requisito é de no máximo 5 ms. Esse pior caso é o do modelo do exercício: uma taxa média de faltas, sozinha, não garante o pior tempo de execução real (WCET).

### A1.3. DSP e Lei de Amdahl

O DSP acelera o filtro em `s = 5` vezes. Como ele ocupa `p = 0,60` do tempo, os outros 40% continuam iguais:

$$
S_{global}=\frac{1}{(1-p)+p/s}
=\frac{1}{0,40+0,60/5}
=\frac{1}{0,52}
\approx\boxed{1,923077}
$$

$$
T_{H+DSP}=T_H\times0,52
=6,875\times0,52
=\boxed{3,575\ ms}
$$

Conferindo por partes: o filtro cai de `6,875 × 0,60 = 4,125 ms` para `4,125/5 = 0,825 ms`. O restante leva `6,875 × 0,40 = 2,750 ms`. Somando: `0,825 + 2,750 = 3,575 ms`.

**Com DSP, a H atende no modelo:** sobram `5 − 3,575 = 1,425 ms`, ou `1,425/5 = 28,5%` do prazo. O ganho total é menor que 5 vezes porque o DSP acelera só o filtro. Na pulseira real, as transferências para o DSP e as interrupções também precisam caber nessa margem.

| Configuração | Processamento calculado | Atraso adicional do SO | Tempo considerado | Atende 5 ms? |
| --- | ---: | ---: | ---: | --- |
| H | 6,875000 ms | 0 ms | 6,875000 ms | Não |
| V | 2,042333 ms | até 3 ms | 5,042333 ms | Não no pior caso do modelo |
| H + DSP | 3,575000 ms | 0 ms | 3,575000 ms | Sim, no modelo |

### A1.4. Por que cache na V e não na H?

Na V, a CPU de 1,2 GHz precisa esperar pela DRAM externa; instruções e dados disputam o acesso à memória, o gargalo de Von Neumann.<br>
A cache reduz essas esperas ao manter por perto instruções e dados usados com frequência [R1].<br>
Na H do enunciado, os caminhos são separados e a SRAM interna responde em um ciclo.<br>
Por isso ela funciona sem cache nessas condições; isso não significa que toda arquitetura Harvard dispense cache.

### A1.5. Evidência das caches e classificação da arquitetura

A coleta foi feita no meu Mac, com **Apple M2, macOS 26.6.2 e arquitetura arm64**. Além de `sysctl -a | grep cachesize`, foram consultados os campos `hw.perflevel`, que separam os núcleos de desempenho e de eficiência. Isso importa porque os dois grupos têm caches de tamanhos diferentes.

![Captura no navegador das saídas reais de sysctl no Mac do autor](img/cache_macos.png)

O [registro completo](img/cache_macos.txt) inclui os comandos e o horário UTC da coleta. O print mostra esse TXT aberto no navegador local; a captura direta do aplicativo Terminal ficou indisponível.

| Grupo observado | Núcleos | L1 de instruções por núcleo | L1 de dados por núcleo | L2 por grupo |
| --- | ---: | ---: | ---: | ---: |
| `perflevel0` — Performance | 4 | 196.608 B = 192 KiB | 131.072 B = 128 KiB | 16.777.216 B = 16 MiB |
| `perflevel1` — Efficiency | 4 | 131.072 B = 128 KiB | 65.536 B = 64 KiB | 4.194.304 B = 4 MiB |

**A L1 é separada em instruções e dados nos dois grupos.** Nas caches, isso corresponde a Harvard modificada. Já o programa usa um espaço de endereçamento e uma memória principal unificados para código e dados, então a classificação nessa visão é **Von Neumann**. Ter L1 separada não torna o computador Harvard puro [R9].

Converti os bytes usando `1 KiB = 1024 B` e `1 MiB = 1.048.576 B`. Segundo a documentação da Apple [R8], `cpusperl2 = 4` indica quatro núcleos compartilhando a L2 de cada grupo. Os campos genéricos `hw.l1icachesize`, `hw.l1dcachesize` e `hw.l2cachesize` mostram o grupo menos performante, sem somar as caches dos núcleos. A coleta não identifica uma L3 ou cache de sistema, por isso não atribuí valores a elas.

## A2. Pipeline: o loop do filtro

### Convenções

Uso os cinco estágios **IF, ID, EX, MEM e WB**, com execução em ordem e sem conflito estrutural entre IF e MEM. Como o banco de registradores escreve na primeira metade do ciclo e lê na segunda, uma instrução pode ler em ID o valor escrito em WB naquele mesmo ciclo.

Considero forwarding para a ALU **e para o dado de `sw`** [R2]. Nos diagramas, `WB*` marca a passagem de `sw` pelo quinto estágio, sem escrever registrador: a gravação ocorre em MEM. IF ou ID repetidos mostram a instrução parada por um stall.

```asm
# Trecho original: identificadores I1 a I7 correspondem às linhas abaixo.
lw   x5, 0(x10)       # I1: amostra nova
add  x6, x6, x5       # I2: soma += nova
lw   x7, 0(x11)       # I3: amostra antiga
sub  x6, x6, x7       # I4: soma -= antiga
sw   x6, 0(x12)       # I5: grava soma
addi x10, x10, 4      # I6: avança ponteiro da nova
addi x11, x11, 4      # I7: avança ponteiro da antiga
```

### A2.1. Dependências RAW

| Instrução produtora | Instrução consumidora | Registrador | Valor necessário |
| --- | --- | --- | --- |
| I1 — `lw` | I2 — `add` | x5 | Amostra nova. |
| I2 — `add` | I4 — `sub` | x6 | Soma após adicionar a amostra nova. |
| I3 — `lw` | I4 — `sub` | x7 | Amostra antiga. |
| I4 — `sub` | I5 — `sw` | x6 | Soma final que deve ser armazenada. |

I5 usa o x6 de **I4**, a última escrita antes da store. A relação I2 → I5 é transitiva. Também preciso manter I1 antes de I6 e I3 antes de I7, para os loads lerem os ponteiros antes de eles mudarem; essas restrições são **WAR**. A contagem considera apenas este trecho, sem dependências de outra iteração.

### A2.2. Sem forwarding

![Pipeline sem forwarding: 17 ciclos](img/pipeline_sem_forwarding.png)

I2 só pode ler x5 no ciclo 5, quando I1 escreve o registrador: são **duas bolhas**. I4 aguarda x6 de I2, disponível no ciclo 8, e x7 de I3, disponível no ciclo 9: a última condição determina a saída, acrescentando **duas bolhas**, sem somar as esperas sobrepostas. I5 aguarda x6 de I4 até o ciclo 12, acrescentando **duas bolhas**.

$$
C_{sem}=n+(k-1)+bolhas=7+(5-1)+2+2+2=\boxed{17\ ciclos}
$$

A contagem vai do IF de I1 no ciclo 1 ao WB de I7 no ciclo 17.

### A2.3. Com forwarding

![Pipeline com forwarding: 13 ciclos](img/pipeline_com_forwarding.png)

Ainda há duas dependências **load-use**: I1 → I2 por x5 e I3 → I4 por x7, cada uma com uma bolha. O primeiro `lw` entrega o dado no fim de MEM, no ciclo 4, então o `add` só o usa em EX no ciclo 5. O segundo `lw` termina MEM no ciclo 7, e o `sub` entra em EX no 8. Mesmo com forwarding, o consumidor precisa esperar a leitura da memória terminar.

As demais dependências são resolvidas pelo encaminhamento, inclusive `sub → sw` para o dado da store:

$$
C_{com}=7+(5-1)+1+1=\boxed{13\ ciclos}
$$

### A2.4. Reordenação sem bolhas

Troco somente as posições de I2 e I3:

```asm
# Reordenação: I1, I3, I2, I4, I5, I6, I7.
lw   x5, 0(x10)       # I1
lw   x7, 0(x11)       # I3: trabalho independente entre lw x5 e add
add  x6, x6, x5       # I2: também separa lw x7 de sub
sub  x6, x6, x7       # I4
sw   x6, 0(x12)       # I5
addi x10, x10, 4      # I6
addi x11, x11, 4      # I7
```

![Pipeline reordenado com forwarding: 11 ciclos](img/pipeline_reordenado.png)

Com essa troca, cada load fica separado do primeiro uso por uma instrução independente. O forwarding resolve `add → sub` e `sub → sw`. Os loads continuam na mesma ordem e antes da store, e os ponteiros só são alterados depois das leituras. Isso preserva o resultado, inclusive se os endereços coincidirem.

$$
C_{reordenado}=7+(5-1)=\boxed{11\ ciclos}
$$

## A3. Processos e threads

### A3.1. Organização proposta para a Plataforma V

Eu manteria **sensor, processamento e motor como três threads de um processo de controle**, criadas na inicialização. O sensor acorda a cada 10 ms e coloca a leitura num buffer limitado; o processamento calcula a resposta; o motor aplica o comando validado. O log fica em segundo plano, sem atrasar a vibração.

As três threads acessam os buffers no mesmo espaço de memória, evitando uma troca por IPC a cada etapa. Cada uma tem sua pilha e seus registradores. A criação e a troca de contexto costumam custar menos do que entre processos separados, embora ainda tenham custo [R3, R4]. O ponto fraco é que uma falha de memória numa thread pode derrubar todo o controle.

O **BLE ficaria num processo separado**, com acesso restrito ao rádio e ao IPC. Ele envia os logs ao celular, recebe configurações de fora e pode falhar ou travar; quero evitar que isso interrompa diretamente o sensor e o motor. Para enviar logs, usaria uma fila IPC de tamanho fixo e sem espera: se estiver cheia, o controle descarta o log e conta a perda. As configurações seriam validadas por tamanho, tipo, faixa e frequência e aplicadas entre amostras. O controle não segura um lock esperando resposta do celular.

Essa organização precisa de testes de latência. Criar threads não elimina os **5,042333 ms** calculados para a V em A1.

### A3.2. Uma falha explorada no BLE

Se o BLE for **uma thread do processo principal**, uma falha que permita executar código dá acesso à memória, aos descritores e às credenciais compartilhados [R4]. Ela pode alterar amostras, configurações e comandos do motor, ou derrubar o processo inteiro. A pilha própria da thread não oferece isolamento de segurança.

Como **processo separado**, o sistema operacional impõe uma fronteira de memória. Para ela servir de proteção, o BLE deve ter permissões mínimas, sem acesso direto ao motor, à memória do controle ou à inspeção desse processo. Ainda preciso autenticar e validar mensagens e limitar sua frequência: um BLE comprometido pode tentar enviar configurações maliciosas ou lotar a fila. Uma falha no kernel também pode romper esse isolamento.

### A3.3. Estados de um processo

![Diagrama de estados: novo, pronto, executando, bloqueado e terminado](img/estados_processo.png)

O processo passa de **novo** para **pronto**, e o escalonador o coloca em **executando**. Se for preemptado, volta a pronto. Se precisar esperar E/S, evento ou temporizador, fica **bloqueado**; quando a espera termina, volta a pronto e aguarda a CPU. Ao concluir, vai para **terminado** [R5].

A **thread do sensor fica a maior parte do tempo bloqueada**, esperando o temporizador ou a interrupção da leitura. Ela publica a amostra e volta a esperar pelo próximo período de 10 ms, sem espera ocupada. Enquanto isso, as outras threads do processo podem executar: cada thread tem seu próprio estado de escalonamento.

## A4. Buffer circular com semáforos

### A4.1. Implementação e método

As três versões estão em [codigo](codigo/) e usam Python 3 com `threading`, **N = 4** e meta de **20.000 amostras**, de `0` a `19.999`. O executor inicia um processo novo para cada teste.

A versão 1 usa espera ocupada para verificar espaço ou amostra disponível. O contador é atualizado em três passos: leitura, `time.sleep(0)` e escrita, sem proteção. Essa pausa permite que a outra thread entre no meio da atualização; o GIL do CPython não torna a sequência inteira indivisível [R6].

Em todas as versões, o consumidor espera **20 ms** no início. Assim o produtor pode encher o buffer, caso que expõe a ordem errada da versão 3. O watchdog usa tempo monotônico e registra travamento após **1 segundo sem consumo**, enquanto a coleta estiver incompleta. A coleta também termina ao atingir **20.000 retiradas**, mesmo que haja duplicatas; nesse caso, a produção pendente é interrompida.

O monitor registra o estado das threads e encerra o processo, sem liberar os semáforos bloqueados. Isso permite terminar o teste, mas não recupera o algoritmo em deadlock. Os ensaios produzem o mais rápido possível para observar concorrência; não simulam os 100 Hz nem medem o prazo de 5 ms do produto.

### A4.2. Definição das métricas

| Métrica | Definição usada |
| --- | --- |
| Consumidas | Quantidade de valores válidos retirados pelo consumidor, contando repetições. |
| Únicas | Quantidade de identificadores distintos válidos recebidos. |
| Perdidas | `20.000 − únicas`: amostras esperadas que não chegaram até o encerramento. |
| Duplicadas | `consumidas − únicas`: ocorrências adicionais de identificadores já recebidos. |
| Geradas | Quantidade de amostras efetivamente inseridas pelo produtor antes de concluir ou parar. |
| Inválidas | Leituras de posições sem um identificador válido; registradas separadamente. |
| Travou | O monitor detectou pelo menos 1 segundo sem consumo, com trabalho ainda pendente. |

**“Perdidas” inclui IDs que ainda não foram produzidos quando o teste encerra.** Por isso, os resultados separam não produzidas de produzidas não recebidas; a coluna não mede apenas sobrescritas no buffer.

### A4.3. Nove execuções reais

<!-- RESULTADOS_A4_INICIO -->
**Ambiente:** meu Mac com Apple M2, macOS 26.6.2 arm64 e CPython 3.15.2. A rodada foi coletada em **06/11/2026, no horário de São Paulo**, com **N = 4** e **20.000 amostras** por execução. Os JSON também guardam os horários em UTC.

| Versão | Execução | Produzidas | Consumidas | Perdidas | Duplicadas | Inválidas | Travou? |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 1 | 1 | 19948 | 20000 | 1912 | 1912 | 0 | Não |
| 1 | 2 | 19950 | 20000 | 1875 | 1875 | 0 | Não |
| 1 | 3 | 19824 | 20000 | 2037 | 2037 | 0 | Não |
| 2 | 1 | 20000 | 20000 | 0 | 0 | 0 | Não |
| 2 | 2 | 20000 | 20000 | 0 | 0 | 0 | Não |
| 2 | 3 | 20000 | 20000 | 0 | 0 | 0 | Não |
| 3 | 1 | 4 | 0 | 20000 | 0 | 0 | Sim |
| 3 | 2 | 4 | 0 | 20000 | 0 | 0 | Sim |
| 3 | 3 | 4 | 0 | 20000 | 0 | 0 | Sim |

O resultado que chama atenção na versão 1 é a coluna **“Travou?” marcada como “Não” nas três execuções**. Olhando só isso e as 20.000 leituras, seria fácil concluir que funcionou. Os identificadores mostram o problema:

- Execução 1: 18088 IDs distintos, 1912 duplicações e 1912 IDs ausentes; destes, 52 não foram produzidos e 1860 foram produzidos, mas não recebidos.
- Execução 2: 18125 IDs distintos, 1875 duplicações e 1875 IDs ausentes; destes, 50 não foram produzidos e 1825 foram produzidos, mas não recebidos.
- Execução 3: 17963 IDs distintos, 2037 duplicações e 2037 IDs ausentes; destes, 176 não foram produzidos e 1861 foram produzidos, mas não recebidos.

Na primeira execução, por exemplo, as 20.000 leituras continham só **18088 IDs distintos**. As **1912 duplicações** completaram a contagem, enquanto faltavam 1912 IDs. O consumidor atingiu a meta de retiradas e o monitor interrompeu o produtor. Portanto, a ausência de travamento não bastou para avaliar a entrega.

Na versão 2, as três sequências foram exatamente `0, 1, 2, …, 19.999`, sem perdas, duplicações, leituras inválidas ou travamentos. Na versão 3, o resultado se repetiu: **quatro amostras produzidas e nenhuma consumida**. Dos 20.000 IDs ausentes, **19.996 não chegaram a ser produzidos e 4 ficaram no buffer**. Os registros mostram o produtor segurando `mutex` enquanto espera `vazio`, e o consumidor esperando `mutex`.

**Validação aprovada:** as contagens das sequências brutas conferem com JSON, CSV e logs. A comparação de toda a sequência FIFO da versão 2 passou nas três repetições.
<!-- RESULTADOS_A4_FIM -->

Os [resultados completos](codigo/resultados/) incluem as sequências e os logs. Os prints abaixo mostram o TXT da primeira execução de cada versão aberto no navegador local, como em A1.5.

![Registro real da primeira execução sem sincronização](img/versao1_execucao1.png)

![Registro real da primeira execução com semáforos corretos](img/versao2_execucao1.png)

![Registro real da primeira execução com aquisição em ordem trocada](img/versao3_execucao1.png)

### A4.4. Região crítica e corrida na versão 1

A região crítica reúne a verificação de disponibilidade, o acesso a `buffer[indice]`, o avanço do índice e a atualização da ocupação. O conflito está no contador: **produtor e consumidor escrevem nele**, mesmo tendo índices próprios.

Exemplo de atualização perdida, com ocupação inicial igual a 1:

| Passo | Produtor | Consumidor |
| --- | --- | --- |
| 1 | Insere uma amostra, avança o índice, lê `ocupadas = 1` e cede a CPU. | — |
| 2 | — | Retira uma amostra e lê `ocupadas = 1`; cede a CPU. |
| 3 | Grava `ocupadas = 2` usando a leitura antiga. | — |
| 4 | — | Grava `ocupadas = 0` usando a leitura antiga. |

O contador deveria terminar em `1 + 1 − 1 = 1`, mas fica em 0. Se as duas últimas escritas acontecerem na ordem inversa, fica em 2. Com a ocupação errada, o produtor pode sobrescrever uma amostra e o consumidor pode reler um valor antigo. Uma thread também pode ficar esperando uma condição que o contador representa incorretamente. Os números variam conforme o escalonamento.

### A4.5. O papel de cada semáforo na versão 2

| Semáforo | Valor inicial | Garantia |
| --- | ---: | --- |
| `vazio` | N = 4 | O produtor só insere após reservar uma vaga; evita sobrescrever uma posição ainda ocupada. |
| `cheio` | 0 | O consumidor só retira após reservar um item publicado; evita consumir uma posição vazia. |
| `mutex` | 1 | Uma thread por vez altera a estrutura e seus índices/contador dentro da região crítica. |

A ordem implementada é [R6, R7]:

```text
# Protocolo do produtor correto
P(vazio)
P(mutex)
inserir amostra e avançar índice
V(mutex)
V(cheio)

# Protocolo do consumidor correto
P(cheio)
P(mutex)
retirar amostra e avançar índice
V(mutex)
V(vazio)
```

A diferença é que a thread **espera por vaga ou item antes de pegar o mutex**. Cada inserção publica um item, e cada retirada devolve uma vaga, mantendo a ocupação entre `0` e `N`. Sem reservas intermediárias, `vazio + cheio = N`; durante uma operação, a vaga ou o item reservado pode ainda não ter sido publicado no outro semáforo.

A verificação compara **toda a sequência recebida** com `list(range(20000))`, incluindo a ordem. A versão 1 mostrou por que contar 20.000 leituras não basta. Os testes apoiam o resultado; a justificativa do algoritmo está nesse protocolo, supondo que as threads continuem sendo escalonadas e não falhem dentro da região crítica.

### A4.6. Por que a versão 3 trava

O produtor troca somente a ordem inicial por `P(mutex); P(vazio)`. Depois de preencher as quatro posições, ele tenta inserir a quinta amostra: adquire `mutex`, mas bloqueia em `vazio`, que está em zero. O consumidor consegue reservar um item em `cheio`, mas bloqueia ao tentar entrar em `mutex`.

Para surgir uma vaga, o consumidor precisa retirar um item. Para fazer isso, precisa do mutex que está com o produtor. Forma-se a **espera circular**, e nenhuma thread chega ao `V` que liberaria a outra [R7]. O watchdog encerra o teste sem resolver o bloqueio. Sem a pausa inicial, esse deadlock ainda seria possível, mas dependeria do escalonamento.

## A5. Deadlock entre I2C, log e BLE

### A5.1. Sequência que leva ao bloqueio

Cada recurso tem uma instância, protegida por semáforo binário. O deadlock pode acontecer nesta ordem:

1. `thread_sensor` executa `P(i2c)` e `le_sensor()`, mantendo I2C.
2. `thread_log` executa `P(log)` e `le_log()`, mantendo o arquivo de log.
3. `thread_config` executa `P(ble)` e `recebe_comando()`, mantendo BLE. Considere que o comando já chegou, de modo que ela avança ao próximo `P`.
4. `thread_sensor` tenta `P(log)` e bloqueia porque o log está com `thread_log`.
5. `thread_log` tenta `P(ble)` e bloqueia porque BLE está com `thread_config`.
6. `thread_config` tenta `P(i2c)` e bloqueia porque I2C está com `thread_sensor`.

![Grafo de alocação de recursos durante o deadlock](img/grafo_deadlock.png)

As setas **recurso → thread** indicam alocação; **thread → recurso**, pedido bloqueado. O ciclo é `I2C → sensor → log → thread_log → BLE → configuração → I2C`. Como cada recurso tem uma única instância, esse ciclo caracteriza o deadlock.

### A5.2. Quatro condições necessárias

| Condição | Como aparece neste código |
| --- | --- |
| Exclusão mútua | Cada semáforo binário admite apenas uma thread no uso de seu recurso. |
| Posse e espera | Cada thread mantém o primeiro recurso enquanto tenta obter o segundo. |
| Ausência de preempção | O recurso só é liberado pelo `V` da thread que o utiliza; o código não o retira à força. |
| Espera circular | Sensor espera log; log espera BLE; configuração espera I2C, mantido pelo sensor. |

As quatro condições coexistem nessa intercalação. Quebrar pelo menos uma delas impede esse deadlock [R10].

### A5.3. Correção 1: prevenção com ordem global

Minha primeira correção seria impor **`i2c < log < ble`** como ordem de aquisição, liberando na ordem inversa. Sensor continua com `i2c → log`, log com `log → ble`, e configuração passa a adquirir `i2c → ble`. Sem pedidos voltando a um recurso de ordem menor, a espera circular não se forma [R10].

Na configuração, eu receberia e validaria o comando com o BLE isolado, liberaria o rádio e só então aplicaria a mudança. Se essa aplicação precisasse dos dois recursos, pegaria `i2c` antes de `ble`. Segurar I2C esperando o celular responder poderia atrasar o sensor indefinidamente.

**Para o usuário**, isso evita o congelamento por esse ciclo. Logs e configurações podem esperar, mas o caminho do sensor não deve ficar preso a uma operação longa de rádio ou arquivo. Ainda é preciso limitar o tempo das regiões críticas para cumprir os 5 ms.

### A5.4. Correção 2: detecção e recuperação

Outra opção é um supervisor registrar quem possui cada recurso e quem está esperando. Um ciclo persistente no grafo de espera permite detectar o deadlock. Timeout ou falta de heartbeat podem disparar a verificação, mas também acontecem por lentidão de E/S, então não bastam como prova [R11].

Para recuperar, o supervisor precisa parar os participantes com segurança, descartar operações incompletas e reinicializar I2C, BLE, filas e semáforos. Se não conseguir encerrar uma thread bloqueada com segurança, reinicia o processo de controle ou usa um watchdog independente para reiniciar o dispositivo. Liberar o semáforo de uma thread ainda viva deixaria o risco de ela voltar a mexer em dados incoerentes.

**Para o usuário**, a pulseira pode voltar a funcionar automaticamente, mas fica um período sem leitura ou vibração válida. Também pode perder logs e a configuração em andamento. Um aviso independente do mutex travado deve sinalizar essa indisponibilidade e orientar a pessoa a parar e recorrer ao apoio habitual. Essa recuperação limita a duração da falha, mas não mantém o prazo de 5 ms enquanto ela ocorre.

# Parte B — Decisão do CTO

## Memorando ao conselho da Tato — Dilema 2

**Escolho a Plataforma H com DSP para produzir a Tato.**

A H básica leva **6,875 ms** por amostra e não cumpre os 5 ms. Com o DSP, cai para **3,575 ms** e deixa **1,425 ms de margem**. A V tem a vantagem das atualizações pela internet, mas chega a **5,042333 ms** com o atraso do Linux. Mesmo passando por pouco, ela ultrapassa o limite do exercício. Para uma pulseira que avisa sobre obstáculos, eu priorizaria a margem da H com DSP.

Isso custa **R$ 37 por unidade: R$ 22 da H e R$ 15 do DSP**. Aceito esse acréscimo porque a H sozinha falha no prazo. Ainda são **R$ 33 a menos que os R$ 70 da V**, mas essa economia em componentes não paga automaticamente desenvolvimento e assistência.

Abro mão do OTA e da flexibilidade do Linux. A parte difícil vem depois da venda: a empresa terá de manter atendimento e atualização por cabo. Quem usa a pulseira pode precisar se deslocar, esperar e ficar sem ela durante o serviço. Eu reservaria parte da economia para assistência e unidades de substituição, incluindo esses gastos no orçamento antes de lançar.

Também não trataria firmware sem Linux como garantia de segurança. Uma falha no BLE ou no firmware pode afetar a vibração, e corrigir presencialmente é mais lento. Exigiria validação de comandos, firmware autenticado e prioridade no atendimento de falhas críticas.

A liberação dependeria de medir o caminho completo no hardware: processamento, transferências e interrupções precisam caber nos **5 ms**. Eu suspenderia o lançamento se esse limite fosse ultrapassado. Mudaria para a V se ela demonstrasse pior caso de **até 4,5 ms** e uma economia de assistência que superasse os **R$ 33 adicionais por unidade**. Nessas condições, a atualização remota passaria a justificar o custo.

---

## Referências e origem dos dados

Os dados das plataformas H e V, os preços e os dilemas vêm do enunciado. As contas usam meus parâmetros, e os resultados dos testes estão no repositório. Usei as referências abaixo para os conceitos de arquitetura e concorrência.

- **[R1]** MIT OpenCourseWare. [6.004 — Caches and the Memory Hierarchy](https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/pages/c14/c14s1/). Fórmula de AMAT e localidade.
- **[R2]** Rodolfo Azevedo, Unicamp. [MC732 — Pipelining and Control Dependencies](https://ic.unicamp.br/en/~rodolfo/Cursos/mc732/2026s2/slides/C04C-branch-prediction/). Pipeline de cinco estágios, forwarding e load-use.
- **[R3]** Remzi H. Arpaci-Dusseau e Andrea C. Arpaci-Dusseau. [OSTEP, cap. 26 — Concurrency: An Introduction](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-intro.pdf). Threads, estado e espaço de endereçamento.
- **[R4]** Linux man-pages. [pthreads(7)](https://man7.org/linux/man-pages/man7/pthreads.7.html). Memória e atributos compartilhados por threads.
- **[R5]** Arpaci-Dusseau e Arpaci-Dusseau. [OSTEP, cap. 4 — The Abstraction: The Process](https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-intro.pdf). Estados e transições de processos.
- **[R6]** Python Software Foundation. [Python 3.12 — threading](https://docs.python.org/3.12/library/threading.html). Semáforos, threads, eventos e GIL.
- **[R7]** Arpaci-Dusseau e Arpaci-Dusseau. [OSTEP, cap. 31 — Semaphores](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-sema.pdf). Buffer limitado e ordem de aquisição.
- **[R8]** Apple Developer Documentation. [Determining system capabilities](https://developer.apple.com/documentation/kernel/1387446-sysctlbyname/determining_system_capabilities). Tamanhos de cache por tipo de núcleo, campos genéricos e compartilhamento da L2.
- **[R9]** Cornell University. [CS 3410 — Caches](https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/caches.html). Separação entre caches de instruções e dados.
- **[R10]** University of Wisconsin–Madison. [CS 537 — Deadlock](https://pages.cs.wisc.edu/~solomon/cs537-old/last/deadlock.html). Condições necessárias e prevenção.
- **[R11]** Arpaci-Dusseau e Arpaci-Dusseau. [OSTEP, cap. 32 — Common Concurrency Problems](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-bugs.pdf). Deadlock, detecção e recuperação.
