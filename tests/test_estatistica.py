"""
Testes do módulo de estatística.

Cada valor esperado pode ser conferido à mão; a conta está no docstring.
"""

import math
from datetime import date

import pytest

from src.estatistica import (
    Z_95,
    ic_garwood,
    ic_taxa_por_100mil,
    ic_wilson,
    pessoa_tempo,
    pessoa_tempo_por_ano,
    razao_taxas,
    taxa_por_100mil,
)


class TestPessoaTempo:
    def test_ano_completo_igual_a_populacao(self):
        """Um ano inteiro contribui com a população do ano."""
        assert pessoa_tempo({2025: 100_000}, date(2025, 1, 1), date(2025, 12, 31)) == 100_000

    def test_meio_ano(self):
        """01/01 a 30/06/2025 = 181 dias de 365; 365.000 x 181/365 = 181.000."""
        resultado = pessoa_tempo({2025: 365_000}, date(2025, 1, 1), date(2025, 6, 30))
        assert resultado == pytest.approx(181_000)

    def test_dois_anos_com_bissexto(self):
        """2024 (366 dias) e 2025 completos somam as duas populações."""
        pop = {2024: 200_000, 2025: 210_000}
        resultado = pessoa_tempo(pop, date(2024, 1, 1), date(2025, 12, 31))
        assert resultado == pytest.approx(410_000)

    def test_ano_sem_populacao_interrompe(self):
        """Sem denominador oficial, nenhuma taxa é calculada."""
        with pytest.raises(KeyError, match="2026"):
            pessoa_tempo({2025: 100_000, 2026: None}, date(2025, 1, 1), date(2026, 3, 31))

    def test_periodo_invertido(self):
        with pytest.raises(ValueError):
            pessoa_tempo({2025: 100_000}, date(2025, 6, 1), date(2025, 1, 1))


class TestTaxa:
    def test_calculo_conhecido(self):
        """100 casos em 200.000 pessoas-ano = 50 por 100 mil."""
        assert taxa_por_100mil(100, 200_000) == pytest.approx(50.0)

    def test_pessoa_tempo_zero(self):
        with pytest.raises(ValueError):
            taxa_por_100mil(10, 0)


class TestGarwood:
    def test_zero_casos(self):
        """k = 0: inferior 0; superior = chi2(0,975; 2)/2 = -ln(0,025) ≈ 3,689."""
        inferior, superior = ic_garwood(0)
        assert inferior == 0.0
        assert superior == pytest.approx(-math.log(0.025), rel=1e-9)

    def test_um_caso_limite_inferior(self):
        """k = 1: inferior = chi2(0,025; 2)/2 = -ln(0,975) ≈ 0,0253."""
        inferior, _ = ic_garwood(1)
        assert inferior == pytest.approx(-math.log(0.975), rel=1e-9)

    def test_intervalo_contem_a_contagem(self):
        inferior, superior = ic_garwood(10)
        assert inferior < 10 < superior

    def test_contagem_negativa(self):
        with pytest.raises(ValueError):
            ic_garwood(-1)

    def test_ic_da_taxa_escala_por_100mil(self):
        """0 casos em 100.000 pessoas-ano: superior = 3,689 por 100 mil."""
        inferior, superior = ic_taxa_por_100mil(0, 100_000)
        assert inferior == 0.0
        assert superior == pytest.approx(-math.log(0.025), rel=1e-9)

    def test_ic_da_taxa_com_cinco_casos(self):
        """
        5 casos em 100.000 pessoas-ano (taxa 5 por 100 mil).

        Inferior: χ²(0,025; 2k = 10)/2 = 3,2470/2 = 1,6235.
        Superior: χ²(0,975; 2k + 2 = 12)/2 = 23,3367/2 = 11,6683.
        Divididos por 100.000 e multiplicados por 100.000, ficam iguais.
        """
        inferior, superior = ic_taxa_por_100mil(5, 100_000)
        assert inferior == pytest.approx(1.6235, abs=1e-4)
        assert superior == pytest.approx(11.6683, abs=1e-4)


class TestWilson:
    def test_zero_em_dez(self):
        """0/10: superior = z²/(n + z²) ≈ 3,8415/13,8415 ≈ 0,2775."""
        inferior, superior = ic_wilson(0, 10)
        assert inferior == 0.0
        assert superior == pytest.approx(0.2775, abs=1e-4)

    def test_metade_e_simetrico(self):
        """5/10: intervalo simétrico em torno de 0,5."""
        inferior, superior = ic_wilson(5, 10)
        assert (0.5 - inferior) == pytest.approx(superior - 0.5)

    def test_total_invalido(self):
        with pytest.raises(ValueError):
            ic_wilson(1, 0)


class TestPessoaTempoPorAno:
    def test_ano_parcial_entra_com_fracao(self):
        """2025 inteiro + 1º semestre de 2026 (181 dias de 365)."""
        pop = {2025: 100_000, 2026: 365_000}
        resultado = pessoa_tempo_por_ano(pop, date(2025, 1, 1), date(2026, 6, 30))
        assert resultado[2025] == pytest.approx(100_000)
        assert resultado[2026] == pytest.approx(181_000)


class TestRazaoTaxas:
    def test_taxas_iguais(self):
        """100 casos nos dois períodos, mesma pessoa-tempo: RT = 1.

        IC = exp(+/- 1,96 x raiz(1/100 + 1/100)) = exp(+/- 0,2772) ≈ (0,758; 1,319).
        """
        rt, inferior, superior = razao_taxas(100, 1e5, 100, 1e5)
        assert rt == pytest.approx(1.0)
        assert inferior == pytest.approx(math.exp(-Z_95 * math.sqrt(0.02)))
        assert superior == pytest.approx(math.exp(Z_95 * math.sqrt(0.02)))

    def test_dobro(self):
        """Mesmos casos em metade da pessoa-tempo: RT = 2."""
        rt, _, _ = razao_taxas(50, 1e5, 50, 5e4)
        assert rt == pytest.approx(2.0)

    def test_contagem_zero_nao_estima(self):
        assert razao_taxas(0, 1e5, 10, 1e5) is None
