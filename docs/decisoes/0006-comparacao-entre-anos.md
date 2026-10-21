# 0006. Comparação entre anos por pessoa-tempo, com análise de sensibilidade sem o ano parcial

**Status:** Substituída em parte pela 0008 (2026-10-19). A razão de taxas passou a usar só os meses comuns; a taxa anualizada de cada ano continua no relatório, como descrição.
**Registro:** 2026-10-18

## Contexto

O último ano do período (2026) tem só seis meses, e os meses finais ainda recebem AIH faturadas com atraso. Comparar a contagem bruta de 2026 com a de um ano completo mostraria uma queda falsa.

Até o commit `5b4e403` (16/10/2026), a comparação era feita entre dois anos, só com os meses presentes nos dois (`_meses_comuns`, usada em `comparar_anos_agua` e `comparar_anos_internacoes`). Esse commit migrou o projeto para o período 2023-2026 e substituiu a comparação de dois anos por séries anuais com pessoa-tempo. As três funções foram removidas. A regra dos meses comuns ainda aparecia nas regras do projeto depois disso, já sem correspondência no código.

## Decisão

- Cada ano tem a sua taxa anualizada, calculada com a pessoa-tempo do próprio ano (`pessoa_tempo_por_ano`, decisão 0002). Um ano parcial entra com a fração de dias observados.
- A comparação é feita contra o primeiro ano da série, pela razão de taxas com IC pelo logaritmo, exp(ln RT ± 1,96 √(1/a + 1/b)) (`razao_taxas` em `src/estatistica.py`). É usada em `serie_anual_internacoes` e `serie_anual_todas_causas` (`src/indicadores/internacoes.py`).
- A razão não é calculada quando um dos anos tem zero casos, porque o método do logaritmo não se aplica. `razao_taxas` devolve `None` nesse caso.
- Nas proporções da água (`serie_anual_agua`), cada ano mostra o percentual de amostras fora do padrão (físico-químicos) ou com presença (microbiológicos), com IC de Wilson e o número de amostras, sem razão entre anos.
- A análise de sensibilidade (`sensibilidade_sem_ano_parcial`) refaz os indicadores principais só com os anos completos, até `ultimo_ano_completo()`, e mostra os dois resultados lado a lado no relatório.
- Nenhum p-valor é apresentado. A sobreposição de intervalos não é tratada como teste de diferença.

## Alternativas

- **Meses comuns entre dois anos (método anterior).** Compara períodos iguais do calendário e neutraliza a sazonalidade, mas joga fora o segundo semestre de todos os anos da comparação e não resolve o atraso de faturamento dos meses finais. A regra voltou com a decisão 0008, aceita, que substitui em parte esta.
- **Contagens brutas por ano.** São simples, mas não comparáveis quando um ano é parcial ou quando a população cresce.
- **Teste de tendência ou regressão de Poisson.** Daria uma medida única de mudança ao longo do tempo, mas o plano de análise é descritivo e não inclui modelos (ver `docs/metodos.md`, desenho).

## Consequências

- A taxa anualizada de 2026 é só descrição (decisão 0008) e pode estar subestimada pelo atraso de faturamento, que a pessoa-tempo não corrige. A sensibilidade sem o ano parcial mostra se a conclusão depende desse ano.
- A taxa anualizada de um semestre inclui só os meses de janeiro a junho. Se a doença for sazonal, a taxa de 2026 reflete essa época do ano e não o ano inteiro.
- A sensibilidade cobre o indicador do período inteiro, e não cada ponto da série anual.
- Anos com zero casos aparecem com a taxa e o IC de Garwood, mas sem razão de taxas.

## Fonte

- Rothman, K. J.; Greenland, S.; Lash, T. L. *Modern Epidemiology*. 3. ed. Filadélfia: Lippincott Williams & Wilkins, 2008. Razão de taxas e intervalo pelo logaritmo.
- Histórico do repositório: commit `5b4e403` ("Atualiza módulos de src/, testes e pipeline para 2023-2026"), que removeu `_meses_comuns`, `comparar_anos_agua` e `comparar_anos_internacoes`.
