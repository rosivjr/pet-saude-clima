"""Fixtures dos testes dos indicadores."""

from datetime import date

import pytest

from src import config

# Valores de referência dos IC, conferidos à mão pelas fórmulas fechadas.
# Wilson (z = 1,96): centro (p + z²/2n) / (1 + z²/n),
#   meia-largura z·√(p(1-p)/n + z²/4n²) / (1 + z²/n).
#   1/4 → 4,6–69,9; 2/3 → 20,8–93,9; 1/2 → 9,5–90,5; 1/3 → 6,1–79,2;
#   0/1 → 0,0–79,3; 2/2 → 34,2–100,0.
# Garwood (por 100 mil, com 100.000 pessoas-ano): χ²(0,025; 2n)/2 e χ²(0,975; 2n+2)/2.
#   n=1 → 0,03–5,57; n=3 → 0,62–8,77.


@pytest.fixture
def periodo_um_ano(monkeypatch):
    """Período de 2025 inteiro, população de 100.000: 100.000 pessoas-ano."""
    monkeypatch.setattr(config, "PERIODO_INICIO", date(2025, 1, 1))
    monkeypatch.setattr(config, "PERIODO_FIM", date(2025, 12, 31))
    monkeypatch.setattr(config, "POPULACAO_ANUAL", {2025: 100_000})
