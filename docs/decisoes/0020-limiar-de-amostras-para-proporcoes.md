# 0020. Proporção de amostras de água com menos de 30 amostras é marcada

**Status:** Aceita
**Registro:** 2026-10-21

## Contexto

As tabelas de amostras de água por área de abrangência, por ponto de coleta e por mês marcam com `[!]` os percentuais com poucas amostras, e a figura 02 mostra só as áreas com base suficiente. O limiar era o mesmo das taxas, `LIMIAR_AMOSTRA_MINIMA = 10`, que tem fonte para contagens de eventos (decisão 0018), mas não para proporções.

Proporção é outro tipo de estimativa, e o NCHS tem um padrão separado para ela. Os padrões para proporções exigem tamanho de amostra mínimo de 30 no denominador e, em pesquisas com desenho complexo, também tamanho efetivo de amostra de pelo menos 30: estimativas abaixo disso são suprimidas. Aqui o tamanho efetivo foi tomado como o número de amostras, porque as amostras de água não vêm de desenho complexo. Com 30 ou mais, o padrão olha ainda a largura do IC 95% (absoluta de 0,30 ou mais: suprime; entre 0,05 e 0,30, suprime se a largura relativa passar de 130%).

## Decisão

Uma constante própria, `LIMIAR_AMOSTRAS_PROPORCAO = 30` em `src/config.py`, para as proporções de amostras de água:

- `conformidade_por_area` (`src/indicadores/territorio.py`): coluna `amostra_suficiente` e, a partir dela, o resumo do cloro por área;
- tabelas com `[!]` em `src/relatorio/territorio.py`;
- áreas da figura 02 (`src/graficos.py`).

`LIMIAR_AMOSTRA_MINIMA` (10) continua para contagens de eventos. Como na decisão 0018, a proporção marcada não é suprimida: fica na tabela com o IC de Wilson.

Os critérios de largura do IC não entram. O padrão do NCHS usa o IC de Korn-Graubard, derivado do de Clopper-Pearson e calculado com o tamanho efetivo de amostra; o projeto usa o de Wilson em toda proporção. Sem desenho complexo, o tamanho efetivo seria o número de amostras. Adotar esses critérios exigiria outro método de IC, que não está no plano de análise.

## Efeito medido (execução de 21/10/2026, mesmos dados)

| Onde | Limiar 10 | Limiar 30 |
|---|---|---|
| Seção 11, resumo do cloro: áreas com base suficiente | 19 | 12 |
| Seção 11, resumo do cloro: suficientes com 100% abaixo do mínimo | 6 | 2 |
| Seção 11, tabela do cloro por área: linhas com `[!]` | 6 | 10 |
| Seção 11, tabela de E. coli por área: linhas com `[!]` | 1 | 6 |
| Seção 11, E. coli, bloco "menor positividade" | Maranhão (31 amostras) e 5 áreas com 10 a 17 amostras, todas com 0% | Maranhão (31 amostras, 0%) e 5 áreas com 46 a 249 amostras, de 6,3% a 16,7% |
| Seção 14, E. coli por mês: meses com `[!]` | 0 | 14 dos 35 meses com coleta |
| Seção 14, E. coli por ponto de coleta: linhas com `[!]` | 4 | 4 |
| Figura 02 (E. coli por área) | áreas com 10 ou mais amostras | só as com 30 ou mais |

Os números de amostras, positivos, percentuais e IC não mudam; mudam as marcas, o resumo das áreas suficientes e quais áreas aparecem no bloco de menor positividade e na figura 02.

## Alternativas

- **Manter 10 como decisão do projeto.** Mantém o relatório, mas sem fonte, e mistura o padrão de taxas com o de proporções.
- **Adotar também os critérios de largura do IC.** Exige trocar o IC de Wilson pelo de Korn-Graubard, o IC que o NCHS usa, nessas tabelas.

## Fonte

- Parker JD, Talih M, Malec DJ, et al. National Center for Health Statistics data presentation standards for proportions. National Center for Health Statistics. *Vital Health Stat* 2(175). 2017. Tabela "NCHS Data Presentation Standards for Proportions", critério "Sample size".
- Decisão 0018, sobre o limiar de eventos para taxas.
