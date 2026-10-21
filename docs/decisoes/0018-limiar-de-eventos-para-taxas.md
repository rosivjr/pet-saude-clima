# 0018. Taxa com menos de 10 eventos é marcada como instável

**Status:** Aceita
**Registro:** 2026-10-21

## Contexto

O relatório marca com `[!]` as taxas e os grupos com poucos casos: internações por grupo, notificações do SINAN e óbitos do SIM. O limiar, `LIMIAR_AMOSTRA_MINIMA = 10` em `src/config.py`, estava no código sem fonte.

Com poucos eventos, a taxa varia muito de um período para outro só por acaso. O National Center for Health Statistics (NCHS), dos Estados Unidos, tem padrões escritos para decidir quando uma taxa é estável o bastante para ser apresentada:

- **até os dados de 2022:** asterisco no lugar da taxa bruta ou específica com menos de 20 óbitos, o que corresponde a um erro-padrão relativo de 23% ou mais. O próprio NCHS diz que o limite de 20 é cômodo, mas arbitrário;
- **a partir dos dados de 2023 (padrão atual):** asterisco com menos de 10 óbitos. Com 10 ou mais, a taxa só é apresentada se a largura relativa do IC 95% (largura dividida pela taxa) for de no máximo 160%.

## Decisão

O projeto segue o padrão atual do NCHS. Uma taxa ou um grupo com menos de 10 eventos (`LIMIAR_AMOSTRA_MINIMA`) recebe o aviso "menos de 10 casos: estimativa instável". O valor continua na tabela, ao lado do IC, porque o relatório é descritivo e mostra, com o IC, o tamanho da incerteza.

O critério da largura relativa não precisa de código próprio. Com o IC exato de Garwood, que o projeto usa em toda taxa, a largura relativa só passa de 160% com 7 eventos ou menos:

| Eventos | IC 95% de Garwood | Largura relativa |
|---|---|---|
| 7 | 2,81–14,42 | 166% |
| 8 | 3,45–15,76 | 154% |
| 9 | 4,12–17,08 | 144% |
| 10 | 4,80–18,39 | 136% |

Toda contagem de 10 ou mais passa, portanto, nos dois critérios.

O limiar vale para contagens de eventos (internações, notificações e óbitos). Proporções de amostras de água seguem outro padrão do NCHS, próprio para proporções (decisão 0020).

## Alternativas

- **20 eventos, a regra anterior do NCHS.** Marcaria mais grupos como instáveis. Foi substituída pelo próprio NCHS a partir dos dados de 2023.
- **Suprimir a taxa, como faz o NCHS.** O NCHS publica estatísticas oficiais; este estudo é descritivo e mostra a contagem e o IC para que o leitor veja a incerteza. A supressão por sigilo de contagens pequenas é outra questão, pendente para a publicação.

## Consequências

- O relatório não muda: o limiar continua 10, agora com fonte.
- O comentário de `LIMIAR_AMOSTRA_MINIMA` em `src/config.py` cita esta decisão.

## Fonte

- Parker JD, Talih M, Irimata KE, Zhang G, Branum AM, Davis D, et al. National Center for Health Statistics data presentation standards for rates and counts. National Center for Health Statistics. *Vital Health Stat* 2(200). 2023.
- Kochanek KD, Murphy SL, Xu JQ, Arias E. Implementation of new data presentation standards for rates and counts for mortality. National Center for Health Statistics, 2024 (https://wonder.cdc.gov/controller/pdf/presentation-standards-mortality-2024.pdf), seção "Suppression of unreliable rates".
