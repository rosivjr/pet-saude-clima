"""
Seções em texto do relatório, montadas a partir de indicadores já calculados.

numero e milhar formatam números também para as figuras.
"""

from ._formato import milhar, numero
from .abastecimento import secao_abastecimento
from .agua import (
    secao_conformidade,
    secao_microbiologica,
    secao_serie_agua,
    secao_serie_anual_agua,
)
from .geral import (
    cabecalho,
    rodape,
    rodape_figura,
    secao_lacunas,
    secao_proveniencia,
    secao_qualidade,
)
from .internacoes import (
    secao_drsai,
    secao_etario_feco_oral,
    secao_perfil_etario,
    secao_perfil_grupos,
    secao_serie_anual_internacoes,
    secao_serie_internacoes,
)
from .mortalidade import secao_mortalidade
from .notificacoes import secao_cobertura_fontes, secao_notificacoes
from .rede import secao_rede
from .saneamento import secao_censo, secao_plano_amostragem, secao_sinisa
from .sazonalidade import secao_precipitacao
from .sensibilidade import secao_sensibilidade
from .territorio import secao_ecoli, secao_territorial

__all__ = [
    "cabecalho",
    "milhar",
    "numero",
    "rodape",
    "rodape_figura",
    "secao_abastecimento",
    "secao_censo",
    "secao_cobertura_fontes",
    "secao_conformidade",
    "secao_drsai",
    "secao_ecoli",
    "secao_etario_feco_oral",
    "secao_lacunas",
    "secao_microbiologica",
    "secao_mortalidade",
    "secao_notificacoes",
    "secao_perfil_etario",
    "secao_perfil_grupos",
    "secao_plano_amostragem",
    "secao_precipitacao",
    "secao_proveniencia",
    "secao_qualidade",
    "secao_rede",
    "secao_sensibilidade",
    "secao_serie_agua",
    "secao_serie_anual_agua",
    "secao_serie_anual_internacoes",
    "secao_serie_internacoes",
    "secao_sinisa",
    "secao_territorial",
]
