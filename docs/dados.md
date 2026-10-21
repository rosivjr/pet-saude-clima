# Dados usados no projeto

Descrição de cada base no modelo de metadados "readme" da Cornell University
(Research Data Management Service Group): informações gerais, acesso,
método de obtenção e, para cada variável usada, nome, unidade, códigos de
ausente e tratamento aplicado.

Nenhum arquivo de dados está no repositório. Os brutos ficam em `data/raw/`
(ou no cache do PySUS, em `~/pysus`) e não são alterados. Os valores fixos
citados abaixo (códigos, limites, períodos) estão em `src/config.py`, pelo
nome da constante. As datas de extração vêm do JSON de proveniência da
execução (`outputs/proveniencia/`), que também guarda o tamanho e o SHA-256 de
cada arquivo lido.

**Recorte comum a todas as bases:** Parauapebas (PA), código IBGE 1505536
(`MUNICIPIO_IBGE_7`; 150553 com 6 dígitos, `MUNICIPIO_IBGE_6`), de 01/01/2023
a 30/06/2026 (`PERIODO_INICIO`, `PERIODO_FIM`). Nas bases de saúde, só
residentes. Só agregados saem do pipeline; nenhum registro individual é
impresso.

<!-- datas:inicio -->
| Base | Arquivos | Extração |
|---|---|---|
| SIH/SUS | RDPA2301 a RDPA2607 (43 meses); da 2026-07 só entram internações com `DT_INTER` até 30/06/2026, fim da análise | 09/09/2026 a 18/10/2026 |
| SINAN | 7 agravos, 2023 a 2026 | 09/09/2026 a 20/10/2026 |
| SINAN hepatites (análise à parte) | HEPABR22, HEPABR23 | 20/10/2026 (HEPABR22); 26/09/2026 (HEPABR23) |
| SIM | DOPA2023, DOPA2024 | 25/09/2026 |
| CNES | STPA2306, STPA2406, STPA2506, STPA2606 | 16/09/2026 a 20/10/2026 |
| SISAGUA, qualidade | sisagua_2023.csv a sisagua_2026.csv | 04/09/2026 a 18/09/2026 |
| SISAGUA, cadastro | sisagua_populacao.csv | 15/09/2026 |
| Censo 2022 (SIDRA) | tabelas 6803, 6805, 6892 | 25/09/2026 |
| SINISA | 2 planilhas, ano de referência 2024 | 25/09/2026 |
| ERA5 (Open-Meteo) | precipitacao_diaria.csv | 25/09/2026 |
<!-- datas:fim -->

As datas são as dos arquivos; o PySUS pode regravar um arquivo sem mudar o
conteúdo. A versão usada é identificada pelo SHA-256 na proveniência.

Os dados de 2025 e 2026 do SIH e do SINAN são preliminares: o DATASUS
atualiza os arquivos, e as contagens dos últimos meses tendem a crescer.

**Reprodutibilidade: o cache do PySUS vem primeiro.** Toda chamada ao PySUS
consulta o catálogo remoto, mesmo quando o arquivo já está no cache: lista os
arquivos e compara o tamanho do local com o do remoto, e baixa de novo se
diferirem. Por isso, desde 21/10/2026, `main.py` lê o SIH, o SINAN, o SIM e o
CNES direto do cache (`PYSUS_PASTA_CACHE`, em
`~/pysus/downloads/ducklake/<sistema>/`) quando o arquivo existe, sem consultar
o servidor. Só o que falta no cache é pedido ao PySUS, como antes. Cada
arquivo lido leva na proveniência o campo `leitura`: "cache local do PySUS,
sem consulta ao servidor" ou "PySUS, com consulta ao servidor".

Assim, duas execuções comuns do `main.py` com o mesmo cache leem os mesmos
arquivos e dão o mesmo relatório. Os dados preliminares só se atualizam pelos
alvos `make baixar-*`, nunca numa execução comum do `main.py`. Atualizar o
cache é uma decisão explícita, e a versão nova aparece pelo SHA-256 na
proveniência.

---

## 1. SIH/SUS — internações hospitalares

**Informações gerais.** Sistema de Informações Hospitalares do SUS, arquivo RD
(AIH reduzida), mensal por UF. Cobre só internações financiadas pelo SUS.

**Acesso.** Público, anonimizado. Baixado pelo PySUS (`pysus.ftp.sih`), da
origem em `PYSUS_SOURCE` (`catalog` = espelho do projeto PySUS; `origin` =
FTP do DATASUS), registrada na proveniência. Competências de 2023-01 a
2026-07. A competência 2026-07 foi baixada, mas a análise termina em
30/06/2026. Como o recorte é por `DT_INTER`, dela só entram as AIH de
internações até essa data, faturadas com atraso; as internações de julho
ficam fora.

**Corte fixo da extração.** Desde 21/10/2026, a última competência pedida ao
PySUS é `config.SIH_ULTIMA_COMPETENCIA`, hoje (2026, 7). Nem `main.py`
(`carregadores.carregar_sih`) nem `make baixar-sih` (`sih/baixar_sih.py`)
pedem competência posterior. Antes, `main.py` pedia os 12 meses de cada ano
de `config.ANOS`, e os meses ainda não publicados faziam a execução depender
do servidor. O relatório diz até onde vai a extração na seção 7 (lacunas de
dados), com a linha "SIH extraído até a competência 2026-07", lida da
constante; ela substitui a lista de competências de 2026-08 a 2026-12, que
saíam como indisponíveis. Para estender a extração, troque a constante e
rode `make baixar-sih`; nada mais muda. As competências nacionais dos scripts
do DDA (`config.SIH_COMPETENCIAS_NACIONAIS`, de 2025-01 a 2026-06) ficam
separadas do corte, para não mudar os números do DDA; a unificação fica para
a reescrita do relatório DDA.

**Método.** Leitura só das colunas de `COLUNAS_SIH` (`src/carregadores.py`)
e só das AIH de residentes (`MUNIC_RES`). Entram só AIH do tipo 1
(`SIH_IDENT_NORMAL`, decisão 0009). O período é contado por `DT_INTER`, não
pela competência do arquivo (decisão 0003); na execução de 20/10/2026, 2.529
AIH de residentes ficaram fora por `DT_INTER` fora do período.

| Variável | Conteúdo | Unidade ou códigos | Tratamento |
|---|---|---|---|
| `N_AIH` | identificador da internação | texto | contagem de duplicidade |
| `IDENT` | tipo de AIH | 1 normal, 5 longa permanência | só 1 |
| `MUNIC_RES` | município de residência | IBGE, 6 dígitos, texto | igual a `MUNICIPIO_IBGE_6_STR` |
| `MUNIC_MOV` | município do hospital | IBGE, 6 dígitos | descrição da rede |
| `DIAG_PRINC` | diagnóstico principal | CID-10 sem ponto (`A090`) | 3 primeiros caracteres; um grupo por internação (decisão 0004) |
| `DIAG_SECUN` | diagnóstico secundário | CID-10 | não entra no grupo |
| `IDADE`, `COD_IDADE` | idade e unidade | 2 dias, 3 meses, 4 anos, 5 = 100 + valor | anos completos; faixas `FAIXA_ETARIA_LIMITES`. Leitura dos códigos a conferir no dicionário |
| `SEXO` | sexo | código do SIH | descrição |
| `DT_INTER`, `DT_SAIDA` | internação e alta | AAAAMMDD | recorte temporal por `DT_INTER` |
| `DIAS_PERM`, `UTI_MES_TO` | permanência e dias de UTI | dias | descrição |
| `MORTE` | óbito na internação | 1 = sim | descrição |
| `CNES` | estabelecimento | código CNES | ligação com o nome em `CNES_NOMES` |
| `CAR_INT` | caráter da internação | urgência ou eletiva | descrição |

**Ausentes.** Campo vazio conta como incompleto na escala de Romero e Cunha
(`ESCALA_INCOMPLETUDE`); nada é removido por incompletude.

## 2. SINAN — notificações compulsórias

**Informações gerais.** Sistema de Informação de Agravos de Notificação, um
arquivo nacional por agravo e ano (ex.: `LEPTBR25`). Agravos lidos em
`SINAN_AGRAVOS`: febre tifoide, cólera, leptospirose, esquistossomose,
chikungunya, zika e acidente por animal peçonhento. Diarreia aguda não é
agravo do SINAN (vigiada pelo Sivep-DDA).

**Acesso.** Público, anonimizado, pelo PySUS (`pysus.ftp.sinan`). Cólera não
tinha arquivo publicado para 2023 nem para 2026. O Sinan hepatites
(análise à parte em `sinan/`) foi extraído em 20/10/2026 (`HEPABR22`) e em
26/09/2026 (`HEPABR23`), datas do `baixado_em` dos JSONs em `data/raw/sinan/`; o
DATASUS publica microdados de hepatites só até 2023 (`SINAN_HEPATITE_ANOS`).
O JSON de proveniência do HEPABR22 diz que o script não baixa nada; na
prática, o PySUS baixou o arquivo de novo ao localizá-lo. A data em
`baixado_em` é a desse novo download, e o SHA-256 identifica a versão usada.

**Método.** Leitura de `COLUNAS_SINAN`, filtro por `ID_MN_RESI`, período por
`DT_NOTIFIC`. Caso é a notificação confirmada pelos códigos de cada ficha em
`SINAN_CLASSI_FIN` (decisão 0001); fichas sem o campo (`SINAN_SEM_CLASSI_FIN`)
são contadas pelas notificações.

| Variável | Conteúdo | Unidade ou códigos | Tratamento |
|---|---|---|---|
| `ID_AGRAVO` | agravo | CID-10 da ficha | grupo via `SINAN_AGRAVOS` |
| `ID_MN_RESI` | município de residência | IBGE, 6 dígitos, texto | igual a `MUNICIPIO_IBGE_6_STR` |
| `DT_NOTIFIC` | data da notificação | data | recorte temporal |
| `DT_SIN_PRI` | primeiros sintomas | data | consistência de datas |
| `NU_ANO` | ano da notificação | ano | conferência |
| `NU_IDADE_N` | idade | 1º dígito: 1 hora, 2 dia, 3 mês, 4 ano | anos completos |
| `CS_SEXO` | sexo | `I` = ignorado | ignorado conta como incompleto |
| `CLASSI_FIN` | classificação final | varia por ficha (chikungunya: 13 confirmado, 5 descartado) | confirmado, descartado, sem classificação |
| `EVOLUCAO` | desfecho | `9` = ignorado | ignorado conta como incompleto |

**Ausentes.** Os códigos de ignorado (`CODIGOS_IGNORADO`) e os de `CLASSI_FIN`
da zika (`SINAN_CLASSI_A_CONFERIR`) ainda precisam de conferência no
dicionário nacional.

## 3. SIM — mortalidade

**Informações gerais.** Sistema de Informações sobre Mortalidade, Declaração de
Óbito, arquivo anual por UF (`DOPAAAAA`).

**Acesso.** Público, pelo PySUS (`pysus.ftp.sim`). Na extração havia só 2023 e
2024; a taxa usa só a pessoa-tempo dos anos com SIM publicado.

**Método.** Leitura de `COLUNAS_SIM`, filtro pelos 6 primeiros dígitos de
`CODMUNRES`, período por `DTOBITO`, grupo pela causa básica.

| Variável | Conteúdo | Unidade ou códigos | Tratamento |
|---|---|---|---|
| `CAUSABAS` | causa básica | CID-10 | 3 primeiros caracteres |
| `CODMUNRES` | município de residência | IBGE | 6 primeiros dígitos |
| `DTOBITO` | data do óbito | data | recorte temporal |
| `IDADE` | idade | 1º dígito: 0 min, 1 h, 2 dia, 3 mês, 4 ano, 5 = 100 + valor | anos completos; conferida na Estrutura do SIM (MS/SVS) em 21/10/2026 |
| `SEXO` | sexo | `0` e `9` = ignorado | incompleto |
| `RACACOR` | raça/cor | não aceita ignorado, só branco | incompleto se vazio |
| `LOCOCOR` | local de ocorrência | `9` = ignorado | incompleto |

## 4. CNES — estabelecimentos de saúde

**Informações gerais.** Cadastro Nacional de Estabelecimentos de Saúde,
subconjunto ST, mensal e substitutivo.

**Acesso.** Público, pelo PySUS (`pysus.ftp.cnes`). Uma competência de junho
por ano (`CNES_COMPETENCIA_MES`), para que cada ano seja descrito com o
próprio cadastro: STPA2306 a STPA2606.

**Método.** Leitura de `COLUNAS_CNES`, filtro por `CODUFMUN`. O tipo de
unidade é traduzido por `CNES_TIPOS_UNIDADE` (lista do CnesWeb, consulta em
25/09/2026); códigos antigos estão marcados como tal.

| Variável | Conteúdo | Unidade ou códigos | Tratamento |
|---|---|---|---|
| `CNES` | código do estabelecimento | 7 dígitos | chave com o SIH |
| `CODUFMUN` | município | IBGE, 6 dígitos | filtro |
| `TP_UNID` | tipo de unidade | `CNES_TIPOS_UNIDADE` | descrição |
| `VINC_SUS`, `LEITHOSP`, `URGEMERG`, `ATENDAMB`, `ATENDHOS` | indicadores | 1 = sim | descrição da rede |
| `NIV_HIER`, `TPGESTAO` | nível e gestão | códigos do CNES | descrição |
| `QTLEITP1` a `QTLEITP3` | leitos | número | soma por estabelecimento |

## 5. SISAGUA — vigilância da qualidade da água

**Informações gerais.** Sistema de Informação de Vigilância da Qualidade da
Água para Consumo Humano, dataset "SISAGUA - Vigilância Parâmetros Básicos",
um CSV nacional por ano, separado por `;`. A unidade de análise é a amostra
de água, não a pessoa.

**Acesso.** Público. Baixado à mão do Portal de Dados Abertos do Ministério da
Saúde (dadosabertos.saude.gov.br) e salvo como `data/raw/sisagua_2023.csv` a
`sisagua_2026.csv` (decisão 0017, que registra o SHA-256 de cada arquivo).

**Método.** Leitura em blocos, só com as colunas usadas e só as linhas do
município (`CO_MUNICIPIO_IBGE`), sem carregar o arquivo inteiro. Limites da
Portaria GM/MS nº 888/2021: cloro residual livre ≥ 0,2 mg/L
(`CLORO_RESIDUAL_MINIMO`), turbidez ≤ 5 uT (`TURBIDEZ_MAXIMA`), pH entre 6,0 e
9,5 (`PH_MINIMO`, `PH_MAXIMO`). Para coliformes totais, a Portaria avalia o
conjunto mensal de amostras do responsável pelo sistema; as amostras do SISAGUA
são da vigilância, e o indicador é o percentual de amostras com presença de
coliformes totais ou de *E. coli* (ver `docs/metodos.md`).

| Variável | Conteúdo | Unidade ou códigos | Tratamento |
|---|---|---|---|
| `CO_MUNICIPIO_IBGE` | município | IBGE, 6 dígitos, inteiro | igual a `MUNICIPIO_IBGE_6` |
| `NU_ANO`, `NU_MES`, `DT_COLETA` | data da coleta | ano, mês, data | recorte temporal |
| `TP_ABASTECIMENTO` | forma de abastecimento | SAA, SAC, SAI | descrição |
| `NU_SOLUCAO_ABASTECIMENTO` | solução de abastecimento | código | chave com o cadastro (decisão 0005) |
| `TP_ZONA`, `NO_AREA`, `NO_CATEGORIA_AREA` | zona e área de abrangência | texto | análise territorial por área (decisão 0014) |
| `TP_PONTO_COLETA`, `TP_LOCAL`, `NO_LOCAL` | ponto e local da coleta | texto | descrição |
| `PARAMETRO` | parâmetro medido | `PARAMETROS_NUMERICOS`, `PARAMETROS_MICROBIOLOGICOS` | seleção |
| `RESULTADO` | resultado | número com vírgula decimal ou PRESENTE/AUSENTE | separado em `resultado_numerico` e `resultado_texto` (decisão 0013); ponto fora do milhar brasileiro interrompe a leitura (decisão 0010) |

**Ausentes.** Resultado vazio ou não numérico não entra no denominador do
parâmetro numérico. Nos microbiológicos, texto diferente de PRESENTE e AUSENTE
conta como não positivo (pendência da decisão 0013). As coordenadas vieram
vazias em 2025 (decisão 0014).

## 6. SISAGUA — cadastro das soluções de abastecimento

**Informações gerais e acesso.** Mesmo portal, arquivo
`data/raw/sisagua_populacao.csv`, uma linha por solução e ano.

**Método.** Filtro por `CO_MUNICIPIO_IBGE`. Cada amostra se liga ao cadastro
pela `NU_SOLUCAO_ABASTECIMENTO`, no ano da coleta; sem cadastro nesse ano, no
ano anterior mais próximo e, por último, no seguinte (decisão 0005). As
contagens de cada tipo de ligação aparecem nas seções 12 e 14 do relatório.

| Variável | Conteúdo | Unidade ou códigos | Tratamento |
|---|---|---|---|
| `NU_ANO` | ano do cadastro | ano | ligação por ano |
| `TP_ABASTECIMENTO` | forma de abastecimento | SAA, SAC, SAI | descrição |
| `NU_SOLUCAO_ABASTECIMENTO`, `NO_SOLUCAO_ABASTECIMENTO` | solução | código e nome | chave; não pode repetir no mesmo ano |
| `NO_EMPRESA` | responsável | texto | descrição |
| `CAPTACAO_SUPERFICIAL`, `CAPTACAO_SUBTERRANEA`, `CAPTACAO_AGUA_CHUVA` | tipo de captação | indicador | amostras com *E. coli* presente por captação |
| `FILTRACAO`, `DESINFECCAO` | tratamento declarado | indicador | divergência entre desinfecção declarada e cloro medido |
| `NU_VALOR_POPULACAO_ESTIMADA`, `NU_VALOR_RURAL`, `NU_VALOR_URBANA` | população abastecida | pessoas | descrição |

## 7. Censo Demográfico 2022 — saneamento dos domicílios

**Informações gerais.** IBGE, domicílios particulares permanentes ocupados.
Tabelas do SIDRA em `CENSO_2022_TABELAS`: 6803 (abastecimento de água), 6805
(esgotamento sanitário) e 6892 (destino do lixo).

**Acesso.** Público, baixado à mão do SIDRA (município Parauapebas, todas as
categorias, CSV) e salvo com os nomes de `CENSO_2022_TABELAS`. Ausente, a
seção fica marcada como indisponível.

**Método.** Percentual de domicílios por categoria. As subcategorias que somam
a linha de cima (`CENSO_2022_SUBCATEGORIAS`) não são somadas de novo. Unidade:
domicílio, não pessoa; não forma série com o SINISA.

## 8. SINISA — indicadores de água e esgoto

**Informações gerais.** Sistema Nacional de Informações em Saneamento Básico,
Ministério das Cidades, SINISA 2025 com ano de referência 2024.

**Acesso.** Público, baixado à mão: as duas planilhas de `SINISA_ARQUIVOS`, em
`data/raw/sinisa/`. A referência nacional está em `SINISA_BRASIL`.

**Método.** Leitura dos indicadores IAG0001 (atendimento de água), IES0001
(atendimento de esgoto), IES2003 (esgoto tratado sobre a água consumida) e
IAG2013. O IES2004, com base no esgoto coletado, não é comparável. Dado
declarado pelo prestador; mede coisa diferente do Censo.

## 9. População — IBGE

**Informações gerais.** Denominador das taxas (`POPULACAO_ANUAL`), com a fonte
de cada ano em `POPULACAO_FONTE` (decisão 0016).

**Acesso e método.** Estimativas do IBGE publicadas no DOU para 2024 (298.854),
2025 (305.771) e 2026 (312.427). O IBGE não publica estimativa municipal para
2023; o projeto usa a média geométrica entre o Censo 2022 (267.836) e a
estimativa de 2024, valor calculado e não oficial. Ano incompleto entra como
pessoa-tempo (decisão 0002).

## 10. Precipitação — ERA5

**Informações gerais.** Reanálise ERA5 do ECMWF (Hersbach et al., 2020), grade
de 0,25° (cerca de 25 km), chuva diária.

**Acesso.** API de histórico do Open-Meteo (`CLIMA_API`, modelo
`CLIMA_MODELO`), baixada automaticamente na primeira execução e guardada em
`data/raw/clima/precipitacao_diaria.csv` com um JSON de proveniência. Com o
arquivo presente e cobrindo o período, nada é baixado de novo.

**Método.** Coordenadas do geocodificador do Open-Meteo a partir do nome do
município (`CLIMA_COORDENADAS = None`), registradas na proveniência. Soma
mensal em mm, no fuso `FUSO_HORARIO`. Descreve o padrão sazonal; não substitui
estação local nem representa a chuva de um bairro.
