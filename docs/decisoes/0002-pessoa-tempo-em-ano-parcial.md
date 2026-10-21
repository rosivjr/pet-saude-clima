# 0002. Pessoa-tempo no denominador quando o período não é um ano completo

**Status:** Aceita
**Registro:** 2026-10-18

## Contexto

O período de análise vai de `PERIODO_INICIO` (1º/01/2023) a `PERIODO_FIM` (30/06/2026). O último ano tem só seis meses. Uma taxa que divide os casos de 2026 pela população inteira de 2026 sai com cerca de metade do valor real e parece uma queda que não existiu. O mesmo problema aparece no indicador do período inteiro, que soma três anos e meio de casos.

A população muda de um ano para outro (`POPULACAO_ANUAL`), então multiplicar uma única população pelo número de anos também distorce o denominador.

## Decisão

O denominador das taxas é a pessoa-tempo, em pessoas-ano. Cada ano civil contribui com a sua população multiplicada pela fração de dias do ano coberta pelo período:

pessoa-tempo = Σ população(ano) × dias observados no ano / dias do ano

No código:

- `pessoa_tempo` (`src/estatistica.py`) faz a soma entre duas datas, inclusive nas duas pontas;
- `pessoa_ano_periodo` (`src/indicadores/_comum.py`) usa essa soma no indicador do período inteiro;
- `pessoa_tempo_por_ano` (`src/estatistica.py`) dá a pessoa-tempo de cada ano da série. Assim, 2026 entra com 181/365 da população do ano, e a taxa anual fica anualizada. Essa taxa é só descrição; a comparação entre anos usa os meses comuns (decisão 0008).

As taxas são dadas por 100 mil pessoas-ano, com IC exato de Garwood calculado sobre a mesma pessoa-tempo.

## Alternativas

- **População de um único ano (por exemplo, Censo 2022) para todo o período.** É simples, mas ignora o crescimento do município, que é rápido em Parauapebas.
- **Taxa só com anos completos.** Joga fora o primeiro semestre de 2026. Essa versão continua existindo como análise de sensibilidade (`sensibilidade_sem_ano_parcial`), mas não como resultado principal.
- **Anualizar multiplicando os casos do ano parcial por 12/6.** Dá o mesmo valor de taxa, mas infla a contagem e deixa o IC estreito demais, porque o IC passa a ser calculado sobre casos que não foram observados.

## Consequências

- A taxa anualizada de 2026 é só descrição (decisão 0008). Ela fica sujeita ao atraso de faturamento dos últimos meses, que a pessoa-tempo não corrige.
- A pessoa-tempo de 2023 depende da população interpolada pelo projeto (`POPULACAO_2023_INTERPOLADA`), que não é um valor oficial do IBGE. Essa limitação consta em `docs/metodos.md`.
- O cálculo é conferido em `tests/test_estatistica.py` com valores feitos à mão. Um exemplo: 365 000 habitantes de 1º/01 a 30/06/2025 dão 365 000 × 181/365 = 181 000 pessoas-ano.

## Fonte

- Rothman, K. J.; Greenland, S.; Lash, T. L. *Modern Epidemiology*. 3. ed. Filadélfia: Lippincott Williams & Wilkins, 2008. Cap. 3, medidas de ocorrência (taxa de incidência com pessoa-tempo no denominador).
- Regra do projeto em `CONTRIBUTING.md`: o denominador é a população do IBGE do ano; se o período não for um ano completo, usar pessoa-tempo.
