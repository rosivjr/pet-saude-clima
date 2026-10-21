"""
Indicadores epidemiológicos e sanitários calculados a partir dos dados padronizados.

Taxas: por 100 mil pessoas-ano no período config.PERIODO_INICIO a
PERIODO_FIM, com IC 95% exato de Poisson (Garwood). Proporções: IC 95% de
Wilson. Fórmulas em estatistica.py.
"""

from ._comum import meses_comuns, pessoa_ano_periodo, ultimo_ano_completo
from .abastecimento import (
    PerfilAbastecimento,
    composicao_cadastro_por_ano,
    divergencia_desinfeccao,
    ecoli_por_captacao,
    ligar_cadastro_por_ano,
    perfil_abastecimento,
    resumo_cloro_areas,
)
from .agua import (
    ResultadoConformidade,
    avaliar_conformidade_agua,
    avaliar_microbiologico,
    serie_anual_agua,
    serie_mensal,
)
from .internacoes import (
    PerfilAgravo,
    indicador_drsai,
    perfil_etario,
    perfil_etario_feco_oral,
    perfil_por_grupo,
    residentes_fora_do_para,
    serie_anual_internacoes,
    serie_anual_todas_causas,
    serie_mensal_internacoes,
)
from .mortalidade import (
    mortalidade_por_faixa,
    mortalidade_por_grupo,
    pessoa_ano_anos,
    serie_anual_mortalidade,
)
from .notificacoes import (
    CruzamentoFontes,
    cruzar_notificacoes_internacoes,
    notificacoes_por_ano,
    perfil_notificacoes,
)
from .rede import (
    PerfilRede,
    capacidade_hospitalar,
    local_de_internacao,
    perfil_rede,
    rede_do_ano,
    serie_rede_por_ano,
)
from .saneamento import (
    cobertura_censo,
    conferir_subcategorias,
    cumprimento_plano_amostragem,
    minimo_mensal_amostras,
)
from .sazonalidade import precipitacao_mensal, sazonalidade_comparada
from .sensibilidade import sensibilidade_sem_ano_parcial
from .territorio import (
    conformidade_por_area,
    ecoli_por_area,
    ecoli_por_ponto,
    sazonalidade_ecoli,
)

__all__ = [
    "CruzamentoFontes",
    "PerfilAbastecimento",
    "PerfilAgravo",
    "PerfilRede",
    "ResultadoConformidade",
    "avaliar_conformidade_agua",
    "avaliar_microbiologico",
    "capacidade_hospitalar",
    "cobertura_censo",
    "composicao_cadastro_por_ano",
    "conferir_subcategorias",
    "conformidade_por_area",
    "cruzar_notificacoes_internacoes",
    "cumprimento_plano_amostragem",
    "divergencia_desinfeccao",
    "ecoli_por_area",
    "ecoli_por_captacao",
    "ecoli_por_ponto",
    "indicador_drsai",
    "ligar_cadastro_por_ano",
    "local_de_internacao",
    "meses_comuns",
    "minimo_mensal_amostras",
    "mortalidade_por_faixa",
    "mortalidade_por_grupo",
    "notificacoes_por_ano",
    "perfil_abastecimento",
    "perfil_etario",
    "perfil_etario_feco_oral",
    "perfil_notificacoes",
    "perfil_por_grupo",
    "perfil_rede",
    "pessoa_ano_anos",
    "pessoa_ano_periodo",
    "precipitacao_mensal",
    "rede_do_ano",
    "residentes_fora_do_para",
    "resumo_cloro_areas",
    "sazonalidade_comparada",
    "sazonalidade_ecoli",
    "sensibilidade_sem_ano_parcial",
    "serie_anual_agua",
    "serie_anual_internacoes",
    "serie_anual_mortalidade",
    "serie_anual_todas_causas",
    "serie_mensal",
    "serie_mensal_internacoes",
    "serie_rede_por_ano",
    "ultimo_ano_completo",
]
