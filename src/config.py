"""
Constantes do projeto: município, período e população; listas CID-10 dos
grupos DRSAI; códigos do SIH, do SINAN, do SIM e do CNES; limites da
Portaria GM/MS nº 888/2021; caminhos de data/; e os recortes dos scripts de
dda/, sih/ e sinan/. Nenhum outro módulo repete esses valores.
"""

import os
from datetime import date
from pathlib import Path

# O IBGE usa código de 7 dígitos (o último é verificador).
# Sistemas do DATASUS usam os 6 primeiros.
MUNICIPIO_NOME = "Parauapebas"
MUNICIPIO_UF = "PA"
# Título único do projeto: README, CITATION.cff, pyproject.toml e cabeçalho do
# relatório (tests/test_documentacao.py confere os três arquivos).
TITULO_PROJETO = (
    f"Agravos relacionados à água e qualidade da água em {MUNICIPIO_NOME} "
    f"({MUNICIPIO_UF}) — PET-Saúde CLIMA, Eixo II"
)
MUNICIPIO_IBGE_7 = 1505536
MUNICIPIO_IBGE_6 = 150553  # o SISAGUA e o Sivep-DDA gravam como inteiro
MUNICIPIO_IBGE_6_STR = "150553"  # o SIH e o SINAN gravam como texto
UF_IBGE = 15  # Pará; o Sivep-DDA grava a UF pelo código do IBGE

# As 27 unidades da federação, na ordem alfabética das siglas (arquivos
# do SIH-RD de todo o país).
UFS = (
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
)  # fmt: skip

ANOS = [2023, 2024, 2025, 2026]

# Período de análise, inclusive nas duas pontas. Definido pela professora:
# todo o intervalo de 2023 a 2026 com dado disponível. O fim é o último dia
# do último mês com internação na base (diagnóstico: 29/06/2026). Os meses
# finais podem estar incompletos por atraso no faturamento das AIH.
PERIODO_INICIO = date(2023, 1, 1)
PERIODO_FIM = date(2026, 6, 30)
# Última competência (ano, mês) do SIH-RD pedida ao PySUS. As competências
# depois do fim do período só trazem AIH de internações do período faturadas
# com atraso. O corte é fixo para que o resultado não dependa do que o
# servidor já publicou; muda só trocando esta constante e rodando
# make baixar-sih (docs/dados.md).
SIH_ULTIMA_COMPETENCIA = (2026, 7)

# Fuso do município: datas da proveniência e série diária de chuva.
FUSO_HORARIO = "America/Belem"

MESES_ABREV = {
    1: "jan",
    2: "fev",
    3: "mar",
    4: "abr",
    5: "mai",
    6: "jun",
    7: "jul",
    8: "ago",
    9: "set",
    10: "out",
    11: "nov",
    12: "dez",
}
MESES_NOME = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}

# Censo Demográfico IBGE 2022; base da interpolação de 2023 (decisão 0016).
POPULACAO_CENSO_2022 = 267_836

# Estimativas oficiais do IBGE publicadas no DOU (referência: 1º de julho).
# 2024: IBGE, Estimativas da População 2024, conforme FAPESPA, Nota
#       Informativa 02/2024.
# 2025: ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2025/
#       estimativa_dou_2025.pdf
# 2026: ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2026/
#       estimativa_dou_2026.pdf
POPULACAO_IBGE_ESTIMATIVA = {
    2024: 298_854,
    2025: 305_771,
    2026: 312_427,
}

# O IBGE não publica estimativa municipal para 2023: as estimativas só são
# feitas nos anos sem Censo, e a série da Tabela SIDRA 6579 pula de 2021
# para 2024. Para 2023 usa-se interpolação geométrica entre o Censo 2022 e
# a estimativa de 2024, tratando os dois como pontos de meio de ano:
#     P2023 = raiz(P2022 x P2024)
# É um valor calculado pelo projeto, não oficial; deve constar nos métodos.
# Alternativa: substituir pelo valor da série Ripsa/CGIAE/SVSA/MS do
# DATASUS TabNet, se a equipe preferir essa fonte.
POPULACAO_2023_INTERPOLADA = round((POPULACAO_CENSO_2022 * POPULACAO_IBGE_ESTIMATIVA[2024]) ** 0.5)

POPULACAO_ANUAL: dict[int, int | None] = {
    2023: POPULACAO_2023_INTERPOLADA,
    **POPULACAO_IBGE_ESTIMATIVA,
}

POPULACAO_FONTE = {
    2023: "Interpolação geométrica Censo 2022 / estimativa IBGE 2024 (cálculo do projeto)",
    2024: "IBGE, Estimativas da População 2024 (DOU, 29/08/2024)",
    2025: "IBGE, Estimativas da População 2025 (DOU)",
    2026: "IBGE, Estimativas da População 2026 (DOU)",
}

# Fonte: FUNASA (2010). Impactos na saúde e no SUS decorrentes de agravos
# relacionados a um saneamento ambiental inadequado. Classificação baseada
# em Cairncross e Feachem (1993): 5 grandes grupos, 15 grupos de causas.
#
# ATENÇÃO: a lista abaixo foi montada a partir de reproduções do quadro da
# FUNASA em documentos secundários. Conferir no PDF original antes da
# versão final, em especial o grupo de geo-helmintos e teníases.
#
# Os códigos são comparados pelos 3 primeiros caracteres, pois o SIH grava
# o CID sem ponto e com o 4º dígito (ex.: 'A090' para A09.0).

# A. Transmissão feco-oral
CID_FECO_ORAL = (
    "A00",  # cólera
    "A02",
    "A03",
    "A04",  # salmoneloses, shigelose, outras bacterianas
    "A06",
    "A07",
    "A08",
    "A09",  # amebíase, protozoários, virais, diarreia presumível
    "A01",  # febres entéricas (tifoide e paratifoide)
    "B15",  # hepatite aguda A
)

# B. Transmitidas por inseto vetor
# A97 (dengue, CID-10 versão 2019) entra junto com A90-A91: o SIM migrou
# para a versão 2019 no fim de 2024 e o SIGTAP/SIH ainda usava A90/A91 em
# março de 2026. Sem os três códigos, parte da dengue se perde.
# A parte do SIGTAP foi conferida na tabela unificada de 03/2026 (tb_cid sem
# A97; docs/metodos.md). A troca do SIM no fim de 2024 não tem fonte
# registrada (commit 5b4e403) e está a conferir: a CID10.DBF do SIM no FTP do
# DATASUS, de 11/05/2020, ainda não tem A97.
CID_VETOR = (
    "A90",
    "A91",
    "A97",  # dengue
    "A95",  # febre amarela
    "B55",  # leishmanioses
    "B74",  # filariose
    "B50",
    "B51",
    "B52",
    "B53",
    "B54",  # malária
    "B57",  # doença de Chagas
)

# C. Transmitidas pelo contato com a água
CID_CONTATO_AGUA = (
    "B65",  # esquistossomose
    "A27",  # leptospirose
)

# D. Relacionadas com a higiene
CID_HIGIENE = (
    "A71",  # tracoma
    "H10",  # conjuntivite
    "B35",
    "B36",  # micoses superficiais
)

# E. Geo-helmintos e teníases
# A CONFIRMAR no original da FUNASA: as reproduções consultadas não
# trazem os códigos deste grupo. Mantida a lista anterior do projeto.
CID_HELMINTOS = (
    "B68",
    "B69",
    "B70",
    "B71",
    "B76",
    "B77",
    "B78",
    "B79",
    "B80",
    "B81",
    "B82",
    "B83",
)

# Arboviroses que não constam da lista FUNASA (anterior à chegada dos
# vírus ao Brasil). Relatadas em bloco próprio.
CID_ARBOVIROSES_EXTRA = (
    "A92",  # chikungunya e outras febres por mosquito
)

# Análise de sensibilidade: códigos que aparecem em listas locais, mas não
# na classificação FUNASA. Nunca somados ao indicador DRSAI.
CID_SENSIBILIDADE = (
    "A05",  # intoxicações alimentares bacterianas
    "E86",  # depleção de volume (desidratação)
    "L00",
    "L01",
    "L02",
    "L03",
    "L04",  # infecções bacterianas de pele
    "L05",
    "L06",
    "L07",
    "L08",
)

# Contexto climático: citados no projeto por relação com período seco e
# queimadas. Fora do DRSAI.
CID_CONTEXTO_CLIMATICO = (
    tuple(f"J{n:02d}" for n in range(23))  # infecções respiratórias agudas
    + tuple(f"J{n:02d}" for n in range(40, 48))  # doenças pulmonares crônicas
    + ("T63",)  # animais peçonhentos
)

# Nomes de grupo usados também fora deste arquivo.
GRUPO_FECO_ORAL = "Feco-oral"
GRUPO_ARBOVIROSES_EXTRA = "Arboviroses fora do DRSAI"
GRUPO_SENSIBILIDADE = "Sensibilidade"
GRUPO_CONTEXTO_CLIMATICO = "Contexto climático"

# Mapa grupo -> códigos, usado para rotular cada internação.
# Um código não pode aparecer em dois grupos (verificado em test_config.py).
GRUPOS_AGRAVO = {
    GRUPO_FECO_ORAL: CID_FECO_ORAL,
    "Inseto vetor": CID_VETOR,
    "Contato com água": CID_CONTATO_AGUA,
    "Higiene": CID_HIGIENE,
    "Geo-helmintos e teníases": CID_HELMINTOS,
    GRUPO_ARBOVIROSES_EXTRA: CID_ARBOVIROSES_EXTRA,
    GRUPO_SENSIBILIDADE: CID_SENSIBILIDADE,
    GRUPO_CONTEXTO_CLIMATICO: CID_CONTEXTO_CLIMATICO,
}

# Grupos que compõem o indicador DRSAI.
GRUPOS_DRSAI = (
    GRUPO_FECO_ORAL,
    "Inseto vetor",
    "Contato com água",
    "Higiene",
    "Geo-helmintos e teníases",
)

# Rótulo da linha que soma os grupos de GRUPOS_DRSAI.
ROTULO_DRSAI = "DRSAI (agregado)"
# Título do bloco dos grupos que ficam fora do indicador, nas internações e no SINAN.
ROTULO_FORA_DRSAI = "Fora do indicador DRSAI"

# Taxa ou grupo com menos eventos que isto (internações, notificações, óbitos)
# leva o aviso de estimativa instável. Padrão do NCHS a partir dos dados de
# 2023: Parker et al., Vital Health Stat 2(200), 2023 (decisão 0018).
LIMIAR_AMOSTRA_MINIMA = 10

# Proporção de amostras de água (por área, ponto de coleta ou mês) com menos
# amostras que isto leva [!] e fica fora do resumo de áreas suficientes, do
# bloco de menor positividade e da figura 02. Padrão do NCHS para proporções,
# critério "Sample size": Parker et al., Vital Health Stat 2(175), 2017
# (decisão 0020).
LIMIAR_AMOSTRAS_PROPORCAO = 30

# COD_IDADE indica a unidade da coluna IDADE. Leitura feita a partir das
# faixas observadas no diagnóstico (código 2: 0 a 30; 3: 1 a 11; 4: 1 a 99;
# 5: 0 a 5). CONFERIR no dicionário de dados do SIH antes de citar.
SIH_COD_IDADE_DIAS = "2"
SIH_COD_IDADE_MESES = "3"
SIH_COD_IDADE_ANOS = "4"
SIH_COD_IDADE_CEM_MAIS = "5"  # idade = 100 + IDADE

# NU_IDADE_N do SINAN: primeiro dígito é a unidade
# (1 = hora, 2 = dia, 3 = mês, 4 = ano).
SINAN_UNIDADES_MENOR_1_ANO = ("1", "2", "3")
SINAN_UNIDADE_ANOS = "4"

# Só AIH tipo 1 (normal) conta como internação. AIH tipo 5 (longa
# permanência) é continuação e duplicaria a contagem.
# Referência: Bittencourt, Camacho e Leal, Cad Saúde Pública 2006;22(1):19-30, p. 26.
SIH_IDENT_NORMAL = "1"

# O relatório lê só os arquivos RD do Pará; internações de residentes em
# hospitais de outras UFs ficam fora. Tamanho medido em 21/10/2026 com
# sih/sih_nacional.py (RD de todas as UFs, competências 2025-01 a 2026-06,
# AIH tipo 1, ano por DT_INTER, residência por MUNIC_RES). Por ano:
# (internações em hospitais fora do Pará, total de internações de residentes).
# Fica como limitação; a leitura das 27 UFs é a decisão 0019 (proposta).
SIH_RESIDENTES_FORA_DO_PARA = {2025: (192, 13_207), 2026: (67, 5_930)}

# Códigos correspondem aos nomes de arquivo do DATASUS (ex.: LEPTBR25).
SINAN_AGRAVOS = {
    "FTIF": ("Febre tifoide", GRUPO_FECO_ORAL),
    "COLE": ("Cólera", GRUPO_FECO_ORAL),
    "LEPT": ("Leptospirose", "Contato com água"),
    "ESQU": ("Esquistossomose", "Contato com água"),
    "CHIK": ("Chikungunya", GRUPO_ARBOVIROSES_EXTRA),
    "ZIKA": ("Zika", GRUPO_ARBOVIROSES_EXTRA),
    "ANIM": ("Acidente por animal peçonhento", GRUPO_CONTEXTO_CLIMATICO),
}

# Lacunas estruturais, que não dependem do ano baixado. Lacunas de
# disponibilidade (arquivo ausente num ano) passam a ser geradas pelo
# carregador a partir da etapa 2, em vez de escritas à mão.
SINAN_LACUNAS = {
    "Doença diarreica aguda": (
        "vigiada pela MDDA no Sivep-DDA (unidades sentinela), não pelo "
        "SINAN; dado a solicitar à SEMSA"
    ),
    "Parasitoses intestinais": (
        "sem agravo correspondente no SINAN; captadas apenas via internação "
        "(grupo geo-helmintos do SIH)"
    ),
}

# Classificação final (CLASSI_FIN) por ficha, conferida nas fontes oficiais
# listadas na decisão 0001. Os códigos variam entre fichas: chikungunya segue
# a ficha de dengue e usa 13 para confirmado. padronizar_sinan cria a coluna
# 'classificacao' com um dos rótulos abaixo.
SINAN_CONFIRMADO = "confirmado"
SINAN_DESCARTADO = "descartado"
SINAN_SEM_CLASSIFICACAO = "sem classificação"  # campo vazio numa ficha que o tem
SINAN_FICHA_SEM_CLASSI = "ficha sem CLASSI_FIN"  # agravos de SINAN_SEM_CLASSI_FIN
SINAN_OUTRO_CODIGO = "outro código"  # código fora da lista conferida
SINAN_CLASSI_FIN = {
    "CHIK": {"13": SINAN_CONFIRMADO, "5": SINAN_DESCARTADO},
    "LEPT": {"1": SINAN_CONFIRMADO, "2": SINAN_DESCARTADO},
    "COLE": {"1": SINAN_CONFIRMADO, "2": SINAN_DESCARTADO},
    "FTIF": {"1": SINAN_CONFIRMADO, "2": SINAN_DESCARTADO},
    "ZIKA": {"1": SINAN_CONFIRMADO, "2": SINAN_DESCARTADO},
}
# Códigos tirados de ficha estadual (e-SUS VS do Espírito Santo), a conferir
# no dicionário nacional; o relatório mostra a ressalva.
SINAN_CLASSI_A_CONFERIR = ("ZIKA",)

# IDADE no SIM: primeiro dígito é a unidade, os dois seguintes o valor
# (0 minutos, 1 horas, 2 dias, 3 meses, 4 anos, 5 = 100 anos ou mais,
# somando o valor); "000" é idade ignorada. Conferido em 21/10/2026 na
# Estrutura do SIM do MS/SVS (arquivo de Mortalidade 2006, campo IDADE) e no
# dicionário da tabela DO da SES-ES (docs/referencias.md).
SIM_IDADE_IGNORADA = "000"
SIM_UNIDADES_MENOR_1_ANO = ("0", "1", "2", "3")
SIM_UNIDADE_ANOS = "4"
SIM_UNIDADE_CEM_MAIS = "5"

# Tipos de estabelecimento (TP_UNID). Descrições da lista de tipos do
# CnesWeb/DATASUS (cnes2.datasus.gov.br, Indicadores > Tipos de
# Estabelecimentos, consulta em 25/09/2026).
CNES_TIPOS_UNIDADE = {
    "01": "Posto de saúde",
    "02": "Centro de saúde / Unidade básica",
    "04": "Policlínica",
    "05": "Hospital geral",
    "07": "Hospital especializado",
    "15": "Unidade mista",
    "22": "Consultório isolado",
    "32": "Unidade móvel fluvial",
    "36": "Clínica / Centro de especialidade",
    "39": "Unidade de apoio diagnose e terapia (SADT isolado)",
    "40": "Unidade móvel terrestre",
    "42": "Unidade móvel de nível pré-hospitalar na área de urgência",
    "43": "Farmácia",
    "50": "Unidade de vigilância em saúde",
    "60": "Cooperativa ou empresa de cessão de trabalhadores na saúde",
    "62": "Hospital/dia isolado",
    "68": "Central de gestão em saúde",
    "69": "Centro de atenção hemoterápica e/ou hematológica",
    "70": "Centro de atenção psicossocial",
    "72": "Unidade de atenção à saúde indígena",
    "73": "Pronto atendimento",
    "74": "Polo academia da saúde",
    "75": "Telessaúde",
    "76": "Central de regulação médica das urgências",
    "77": "Serviço de atenção domiciliar isolado (home care)",
    "79": "Oficina ortopédica",
    "80": "Laboratório de saúde pública",
    "81": "Central de regulação do acesso",
    "82": "Central de notificação, captação e distribuição de órgãos estadual",
    "83": "Polo de prevenção de doenças e agravos e promoção da saúde",
    "84": "Central de abastecimento",
    "85": "Centro de imunização",
    # Códigos que não estão na lista atual do CnesWeb, mas aparecem em
    # competências antigas. 67 foi substituído pelo 80 (Portaria Conjunta
    # nº 01, de 06/09/2013, citada no manual de preenchimento do CNES);
    # 71 consta do mesmo manual. 20, 21 e 61 conferidos em 21/10/2026 na
    # tabela de tipos de estabelecimento da Ficha 01 do CNES reproduzida pela
    # SMS de Santos (Orientações de preenchimento da FCES, maio/2021).
    "67": "Laboratório central de saúde pública (código antigo, hoje 80)",
    "71": "Centro de apoio à saúde da família (código antigo)",
    "20": "Pronto socorro geral (código antigo)",
    "21": "Pronto socorro especializado (código antigo)",
    "61": "Centro de parto normal isolado (código antigo)",
}

# Uma competência por ano do período, sempre no mesmo mês, para que a rede
# de 2023 não seja descrita com o cadastro de 2026. O cadastro do CNES é
# mensal e substitutivo.
CNES_COMPETENCIA_MES = 6

# Competência usada nas seções que descrevem a rede atual.
CNES_COMPETENCIA_ANO = max(ANOS)

CNES_NOMES = {
    "2615746": "Hospital Geral de Parauapebas Manoel Evaldo Benevides Alves",
    "4705335": "Hospital Rafah",
    "2614634": "Hospital Santa Terezinha",
    "4831543": "Hospital Cristo",
    "2615762": "Hospital São Sebastião",
    "0823783": "Clínica Popular",
    "0265608": "Maternar",
}

# Limites da Portaria GM/MS nº 888, de 04/05/2021.
CRITERIO_PORTARIA_888 = "Portaria GM/MS nº 888, de 04/05/2021"
CLORO_RESIDUAL_MINIMO = 0.2  # mg/L (art. 32)
TURBIDEZ_MAXIMA = 5.0  # uT
PH_MINIMO = 6.0
PH_MAXIMO = 9.5

# Nomes dos parâmetros como gravados na coluna PARAMETRO do SISAGUA.
PARAMETRO_TURBIDEZ = "Turbidez (uT)"
PARAMETRO_PH = "pH"
PARAMETRO_CLORO = "Cloro residual livre (mg/L)"
PARAMETRO_COLIFORMES = "Coliformes totais"
PARAMETRO_E_COLI = "Escherichia coli"
PARAMETROS_NUMERICOS = (PARAMETRO_TURBIDEZ, PARAMETRO_PH, PARAMETRO_CLORO)
PARAMETROS_MICROBIOLOGICOS = (PARAMETRO_COLIFORMES, PARAMETRO_E_COLI)

# Resultado qualitativo dos microbiológicos, já em caixa alta (resultado_texto).
RESULTADO_PRESENTE = "PRESENTE"
RESULTADO_AUSENTE = "AUSENTE"

# Único uso aceito do ponto em RESULTADO: milhar brasileiro com vírgula
# decimal ('1.234,56'). Qualquer outro ponto interrompe a conversão (decisão 0010).
PADRAO_MILHAR_BRASILEIRO = r"^-?[1-9]\d{0,2}(?:\.\d{3})+,\d+$"

# Diretriz Nacional do Plano de Amostragem da Vigilância da Qualidade da
# Água para Consumo Humano (Ministério da Saúde, 2016). Número mínimo
# mensal de amostras de cloro residual livre, turbidez e coliformes
# totais/E. coli, por faixa populacional:
#     (limite superior da faixa, amostras fixas, habitantes por amostra extra)
# Uma faixa com habitantes_por_extra None não tem parcela variável.
PLANO_AMOSTRAGEM_FAIXAS = (
    (5_000, 6, None),
    (10_000, 9, None),
    (50_000, 8, 7_500),
    (200_000, 10, 10_000),
    (500_000, 20, 20_000),
    (None, 35, 50_000),
)

# A Diretriz fala em "1 amostra a cada N habitantes" sem fixar o
# arredondamento. "cima" conta a fração como amostra inteira (mais
# exigente); "baixo" descarta a fração. CONFIRMAR com a SEMSA/SESPA qual
# regra consta do plano municipal aprovado.
PLANO_AMOSTRAGEM_ARREDONDAMENTO = "cima"

# Parâmetros do plano básico cobertos pelo SISAGUA do projeto. Fluoreto
# também faz parte do plano básico, mas não está nos arquivos baixados.
PLANO_AMOSTRAGEM_PARAMETROS = (
    PARAMETRO_CLORO,
    PARAMETRO_TURBIDEZ,
    PARAMETRO_COLIFORMES,
)

# Perfil sanitário: arquivos baixados manualmente.
# Censo 2022, SIDRA/IBGE: domicílios particulares permanentes ocupados.
CENSO_2022_TABELAS = {
    "agua": ("censo2022_6803_agua.csv", "Tabela 6803 — abastecimento de água"),
    "esgoto": ("censo2022_6805_esgoto.csv", "Tabela 6805 — esgotamento sanitário"),
    "lixo": ("censo2022_6892_lixo.csv", "Tabela 6892 — destino do lixo"),
}

# Categorias do SIDRA que são subdivisões da linha anterior sem usar
# " - " no nome. Conferido pela soma: as subcategorias somam a categoria
# de cima (ex.: 19.623 + 5.219 = 24.842 no esgotamento de Parauapebas).
CENSO_2022_SUBCATEGORIAS = {
    "esgoto": {
        "Rede geral ou pluvial",
        "Fossa séptica ou fossa filtro ligada à rede",
    },
    "lixo": {
        "Coletado no domicílio por serviço de limpeza",
        "Depositado em caçamba de serviço de limpeza",
    },
}

# SINISA, Ministério das Cidades: relatórios de indicadores do município.
SINISA_ARQUIVOS = {
    "agua": "sinisa/indicadores_de_abastecimento_de_agua.xlsx",
    "esgoto": "sinisa/indicadores_de_esgotamento_sanitário.xlsx",
}

# Brasil, SINISA 2025 (ano de referência 2024), Ministério das Cidades.
# IAG0001 e IAG2013: Relatório de Abastecimento de Água; IES0001 e IES2003:
# Relatório de Esgotamento Sanitário. O IES2003 tem como base a água
# consumida; o IES2004, com base no esgoto coletado, não é comparável.
SINISA_BRASIL = {"IAG0001": 84.1, "IES0001": 62.3, "IES2003": 51.8, "IAG2013": 39.5}

# Usados só pelos scripts de dda/, sih/ e sinan/ (relatório DDA, hepatite A e saneamento).
# Sivep-DDA (Saldanha, 2026, Zenodo): casos semanais de doença diarreica
# aguda por município. O caso é a soma das faixas etárias.
DDA_ANOS = (2025, 2026)
DDA_FAIXAS = ["nu_m1ano", "nu_1a4", "nu_5a9", "nu_10oumais", "nu_faixign"]
DDA_PLANOS = ["nu_planoa", "nu_planob", "nu_planoc", "nu_planoign"]
# Colunas lidas do parquet do Sivep-DDA: as usadas pelos scripts de dda/.
# uf_sigla e municipio_nome só aparecem na listagem de correções de
# limpeza_dda.corrigir_unidades.
DDA_COLUNAS = [
    "sem_epid_year",
    "sem_epid_week",
    "uf_ibge",
    "uf_sigla",
    "municipio_ibge",
    "municipio_nome",
    "nu_usaude_sem",
    "nu_unidades_inf",
    "lo_surto",
    *DDA_FAIXAS,
    *DDA_PLANOS,
]
DDA_SE_MAX = 22  # última semana do último ano de DDA_ANOS com registro de Parauapebas
DDA_SE_ATRASO_INICIO = 21  # semanas do último ano sujeitas a atraso de digitação
# Depósito do Sivep-DDA no Zenodo (Saldanha, 2026).
DDA_ZENODO_REGISTRO = "https://zenodo.org/api/records/20752301"
DDA_ZENODO_DOI = "https://doi.org/10.5281/zenodo.20752301"
# Número de unidades do Sivep-DDA acima deste múltiplo da mediana do município
# no ano é tratado como erro de digitação e trocado pela mediana. Critério do
# projeto, sem fonte oficial; a sensibilidade de 10 a 1000x está na decisão 0021.
DDA_LIMITE_MEDIANA_UNIDADES = 100

# Competências do SIH-RD de todas as UFs lidas para o relatório DDA, com os
# arquivos em PYSUS_PASTA_SIH. Separadas de SIH_ULTIMA_COMPETENCIA: alimentam
# só os scripts do DDA, e juntá-las mudaria os números do DDA. A unificação
# fica para a reescrita do relatório DDA.
SIH_COMPETENCIAS_NACIONAIS = {2025: range(1, 13), 2026: range(1, 7)}
# Meses comparados na Figura 4 de sih/figuras_sih.py (proporção de
# internações por diarreia no SIH nacional): janeiro a abril, porque as AIH
# de maio e junho de 2026 ainda chegam com atraso de faturamento. O recorte
# veio com o script, no commit 840863d (16/10/2026), sem justificativa
# escrita. O relatório principal compara janeiro a junho (decisão 0008); a
# escolha volta a ser decidida na reescrita do relatório DDA.
SIH_MESES_COMPARACAO = range(1, 5)

SINAN_HEPATITE_ANOS = (2022, 2023)  # Sinan hepatites: microdados publicados só até 2023
# Hepatite A confirmada no Sinan hepatites virais: CLASSI_FIN 1 (confirmação
# laboratorial) ou 2 (confirmação clínico-epidemiológica), campo 48 do
# Dicionário de Dados Sinan NET versão 5.0, Hepatites Virais (MS/SVS,
# revisado em julho de 2010), com HAV = 1 (vírus A). É o critério da nota 1
# da Tabela 3 do boletim abaixo.
# O arquivo público não traz CLAS_ETIOL (campo 50 do dicionário), e sim uma
# coluna por vírus (HAV, HBV, HCV, HDV, HEV); a sorologia anti-HAV IgM fica
# em ANTIHAVIGM. PENDÊNCIA: o dicionário não documenta que HAV desdobra a
# CLAS_ETIOL. A leitura vem das contagens de 2022 e 2023: HAV = 1 só aparece
# com CLASSI_FIN 1 ou 2, inclusive com anti-HAV IgM não reagente ou não
# realizado (confirmação clínico-epidemiológica).
SINAN_HEPATITE_CONFIRMADO = ("1", "2")
SINAN_HAV_VIRUS_A = "1"
# Casos confirmados de hepatite A por ano de diagnóstico, para conferência:
# Boletim Epidemiológico de Hepatites Virais, número especial, julho de 2025
# (SVSA/MS), Tabela 3, p. 40. Casos notificados até 31/12/2024.
SINAN_HEPATITE_A_BOLETIM = {
    2022: {"Brasil": 858, "Pará": 21},
    2023: {"Brasil": 2240, "Pará": 35},
}

# CIDs das internações do relatório DDA, comparados pelos 3 primeiros
# caracteres. São recortes deste relatório, não os grupos DRSAI acima.
CID_RELATORIO_DDA = {
    "diarreia": tuple(f"A0{i}" for i in range(10)),
    "hepatite_a": ("B15",),
    "desidratacao": ("E86",),
    "gastro_nao_infecciosa": ("K52",),
}

# Enquanto não houver série de estação (INMET ou ANA/SEMAS), a chuva vem
# da reanálise ERA5 (ECMWF, grade de 0,25°, cerca de 25 km), pela API de
# histórico do Open-Meteo. Reanálise estima a chuva por modelo; a própria
# documentação do Open-Meteo recomenda medição local quando disponível.
# Serve para descrever o padrão sazonal, não a chuva de um bairro.
# O ERA5-Land (0,1°) foi testado e voltou sem precipitação nessa API; a
# documentação do Open-Meteo descreve o ERA5-Land como focado em variáveis
# de superfície (temperatura, umidade, solo).
# Referência do conjunto: Hersbach H. et al. The ERA5 global reanalysis.
# Q J R Meteorol Soc. 2020;146:1999-2049.
CLIMA_API = "https://archive-api.open-meteo.com/v1/archive"
CLIMA_GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"
CLIMA_MODELO = "era5"
CLIMA_FUSO = FUSO_HORARIO

# Coordenadas do ponto da série (latitude, longitude). None: obtidas pelo
# geocodificador do Open-Meteo a partir do nome do município e da UF, e
# registradas na proveniência e no relatório.
CLIMA_COORDENADAS: tuple[float, float] | None = None

# Cópia local da série baixada. Com o arquivo presente e cobrindo o
# período, nada é baixado de novo.
CLIMA_ARQUIVO = "clima/precipitacao_diaria.csv"

# Escala de incompletude (campo em branco ou ignorado) de Romero e Cunha:
# Romero DE, Cunha CB. Cad Saúde Pública. 2006;22(3):673-681.
# (limite superior exclusivo em %, classificação)
ESCALA_INCOMPLETUDE = (
    (5, "excelente"),
    (10, "bom"),
    (20, "regular"),
    (50, "ruim"),
    (None, "muito ruim"),
)

# Códigos tratados como "ignorado" em cada campo. SIM conferido em 21/10/2026
# na Estrutura do SIM do MS/SVS (2006): SEXO 0 ignorado (o 9 não consta e fica
# como proteção), LOCOCOR 9 ignorado, RACACOR sem código de ignorado (só
# branco). SINAN a conferir no dicionário da notificação individual (CS_SEXO);
# EVOLUCAO muda de ficha para ficha (na de LV, versão 5.0, não há 9).
CODIGOS_IGNORADO = {
    "SINAN": {"CS_SEXO": {"I"}, "EVOLUCAO": {"9"}},
    "SIM": {"SEXO": {"0", "9"}, "LOCOCOR": {"9"}},
}

# Agravos do SINAN sem CLASSI_FIN: o arquivo de animal peçonhento não traz a
# coluna, e a ficha de esquistossomose não tem o campo (SVS, 08/10/2009).
# São contados pelas notificações (decisão 0001) e ficam fora da
# completitude desse campo.
SINAN_SEM_CLASSI_FIN = ("Acidente por animal peçonhento", "Esquistossomose")

# Intervalos fechados à direita: (-1, 0] = menor de 1 ano, (0, 4] = 1-4...
# O limite inferior -1 garante que a idade 0 entre na primeira faixa.
FAIXA_ETARIA_LIMITES = (-1, 0, 4, 9, 14, 19, 29, 39, 49, 59, 69, 79, 130)
# Rótulos de sexo, comuns ao SIH, ao SINAN e ao SIM.
SEXO_MASCULINO = "Masculino"
SEXO_FEMININO = "Feminino"

FAIXA_ETARIA_ROTULOS = (
    "<1",
    "1-4",
    "5-9",
    "10-14",
    "15-19",
    "20-29",
    "30-39",
    "40-49",
    "50-59",
    "60-69",
    "70-79",
    "80+",
)

RAIZ = Path(__file__).resolve().parent.parent
DADOS_BRUTOS = RAIZ / "data" / "raw"
DADOS_INTERMEDIARIOS = RAIZ / "data" / "interim"
DADOS_PROCESSADOS = RAIZ / "data" / "processed"
FIGURAS = RAIZ / "figuras"
# Número máximo de áreas na figura de E. coli por área (graficos.py).
FIGURA_ECOLI_MAX_AREAS = 12

# Paleta das figuras (src/graficos.py, dda/ e sih/figuras_sih.py), derivada
# da identidade visual do PET-Saúde CLIMA.
TEAL = "#2E9CA8"
TEAL_ESCURO = "#14666E"
VERMELHO = "#C0272D"
CINZA = "#5F7378"
COR_EIXOS = "#DDE8E9"  # linhas dos eixos à esquerda e embaixo
# Paleta Okabe-Ito, legível para as formas comuns de daltonismo. O azul é a
# cor única nas barras de percentual: nenhuma norma define faixas de cor.
AZUL_OKABE_ITO = "#0072B2"
LARANJA_OKABE_ITO = "#E69F00"
VERDE_OKABE_ITO = "#009E73"
VERMELHAO_OKABE_ITO = "#D55E00"
# Uma cor por recorte nas figuras de dda/ e de sih/figuras_sih.py.
CORES_LOCAL = {
    MUNICIPIO_NOME: AZUL_OKABE_ITO,
    "Pará": LARANJA_OKABE_ITO,
    "Brasil": VERDE_OKABE_ITO,
}
SAIDAS = RAIZ / "outputs"
PROVENIENCIA = SAIDAS / "proveniencia"

# Origem dos dados no PySUS: "catalog" lê o espelho S3 do projeto PySUS;
# "origin" consulta o FTP do DATASUS. O valor usado fica registrado na
# proveniência de cada execução.
PYSUS_SOURCE = "catalog"
# Endereço de cada origem, gravado na proveniência. O PySUS devolve só o
# caminho local do arquivo, sem a URL exata; o registro guarda o endereço
# da origem e os parâmetros da consulta, que identificam o arquivo.
PYSUS_ENDERECOS = {
    "catalog": "s3://pysus em nbg1.your-objectstorage.com (espelho do projeto PySUS)",
    "origin": "ftp://ftp.datasus.gov.br (servidor do DATASUS)",
}
# Cache local do PySUS: ~/pysus, ou a pasta da variável PYSUS_CACHEPATH, como
# no próprio PySUS, mais a subpasta da origem. Com "catalog" os arquivos
# ficam em downloads/ducklake/<sistema>/ (ex.: sih/RDPA2501.parquet). Com
# "origin", o PySUS grava o arquivo solto na raiz do cache, sem pasta por
# sistema, e o projeto não tem como achá-lo. O carregador lê daqui quando o
# arquivo já existe, sem consultar o servidor; dados preliminares só se
# atualizam pelos alvos make baixar-* (docs/dados.md).
PYSUS_SUBPASTA_CACHE = {"catalog": Path("downloads") / "ducklake"}
if PYSUS_SOURCE not in PYSUS_SUBPASTA_CACHE:
    raise ValueError(
        f"PYSUS_SOURCE {PYSUS_SOURCE!r} sem pasta de cache conhecida; o cache local "
        f"só é lido com {sorted(PYSUS_SUBPASTA_CACHE)}. Acrescente a subpasta dessa "
        "origem em PYSUS_SUBPASTA_CACHE."
    )
PYSUS_PASTA_CACHE = (
    Path(os.environ.get("PYSUS_CACHEPATH", Path.home() / "pysus"))
    / PYSUS_SUBPASTA_CACHE[PYSUS_SOURCE]
)
PYSUS_PASTA_SIH = PYSUS_PASTA_CACHE / "sih"
