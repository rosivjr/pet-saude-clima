# 0003. Recorte temporal do SIH pela data de internação (DT_INTER)

**Status:** Aceita
**Registro:** 2026-10-18

## Contexto

O DATASUS publica o SIH/SUS (AIH reduzida, RD) em arquivos mensais por UF, organizados pela competência de faturamento, e não pela data em que a internação aconteceu. Uma AIH pode ser apresentada meses depois da alta. Assim, o arquivo de uma competência traz internações de meses anteriores e deixa de fora internações do próprio mês que ainda não foram faturadas.

Se o período fosse definido pelos arquivos baixados, uma internação de dezembro de 2022 faturada em janeiro de 2023 entraria no estudo, e uma de junho de 2026 faturada em agosto ficaria de fora.

## Decisão

A internação entra no período pela data de internação, `DT_INTER`, e não pela competência do arquivo:

- `carregar_sih` (`src/carregadores.py`) baixa os arquivos de todas as competências dos anos de `ANOS` e aplica só o filtro de residência;
- `padronizar_sih` (`src/transformacoes.py`) converte `DT_INTER` em data e deriva dela `ano` e `mes`;
- `filtrar_periodo` (`src/transformacoes.py`) mantém só as internações entre `PERIODO_INICIO` e `PERIODO_FIM`. As que ficam fora do período e as que têm data inválida são contadas separadamente e anotadas na proveniência.

As competências baixadas depois de `PERIODO_FIM` servem só para captar internações do período faturadas com atraso. O relatório lista as que ainda não foram publicadas.

## Alternativas

- **Recorte pela competência (`ANO_CMPT` e `MES_CMPT`).** Simplifica a leitura, porque cada arquivo vira um mês, mas mede faturamento, e não ocorrência, e desloca os casos no tempo, o que atrapalha a série mensal e a sazonalidade.
- **Recorte pela data de saída (`DT_SAIDA`).** É coerente com o momento em que a AIH fecha, mas desloca as internações longas para o mês da alta e não corresponde ao início da doença.

## Consequências

- Os meses finais do período ficam incompletos até o faturamento atrasado chegar. A contagem desses meses tende a crescer nas próximas extrações. A decisão 0008, aceita, compara os anos só nos meses comuns, mas não corrige esse atraso.
- Os números não batem com tabulações do TabNet por competência. Quem conferir com o TabNet precisa tabular por mês de internação.
- Internações com `DT_INTER` anterior a `PERIODO_INICIO`, presentes nos arquivos de 2023, são descartadas e contadas na proveniência.
- A decisão aparece na seção de limitações do relatório ("o recorte temporal foi feito pela data de internação") e em `docs/metodos.md`, seção "Participantes (item 6)".

## Fonte

- Bittencourt, S. A.; Camacho, L. A. B.; Leal, M. C. O Sistema de Informação Hospitalar e sua aplicação na saúde coletiva. *Cadernos de Saúde Pública*, Rio de Janeiro, v. 22, n. 1, p. 19-30, 2006. Revisão sobre usos e limitações do SIH em pesquisa.
- Ministério da Saúde. DATASUS. Informações de Saúde (TabNet): notas técnicas do SIH/SUS (variáveis `DT_INTER`, `ANO_CMPT` e `MES_CMPT`).
