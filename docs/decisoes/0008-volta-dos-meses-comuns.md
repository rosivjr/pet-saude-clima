# 0008. Volta dos meses comuns na comparação entre anos, por causa do atraso de faturamento do SIH

**Status:** Aceita (aplicada em 2026-10-19)
**Registro:** 2026-10-18

## Contexto

A comparação entre anos usa hoje taxas anualizadas por pessoa-tempo (decisão 0006). A pessoa-tempo corrige o tamanho do período, mas não o atraso de faturamento. Uma AIH pode ser apresentada meses depois da alta. Por isso, os últimos meses do período (até `PERIODO_FIM`, 30/06/2026) têm menos internações registradas do que de fato aconteceram, e a contagem cresce a cada nova extração (decisão 0003).

A taxa anualizada de 2026 junta dois problemas. Ela cobre só de janeiro a junho, que não é uma amostra representativa de um agravo sazonal. E os meses mais recentes desse semestre estão incompletos. Comparada com um ano completo, ela pode sugerir uma queda que é só artefato do registro.

Até o commit `5b4e403`, o projeto comparava os anos só nos meses presentes nos dois (`_meses_comuns`). A regra foi removida na migração para 2023-2026 (decisão 0006).

## Decisão

Voltar a comparar os anos só nos meses do calendário presentes em todos os anos comparados. Com o período atual, isso significa janeiro a junho de 2023, 2024, 2025 e 2026. A taxa de cada ano continua por pessoa-tempo, agora calculada só sobre os meses comuns, e a razão de taxas segue o método da decisão 0006.

A série anual com os anos completos continua no relatório, como descrição. A comparação com meses comuns passa a ser a que sustenta frases do tipo "aumentou" ou "diminuiu".

## Alternativas

- **Manter só a anualização por pessoa-tempo (decisão 0006).** É mais simples e usa todos os dados, mas compara semestres diferentes do ano e não trata o atraso.
- **Excluir do período os meses mais recentes ainda sujeitos a atraso.** Trataria o atraso diretamente, mas exige definir quantos meses excluir. Esse critério precisa vir de uma fonte (por exemplo, a distribuição observada do atraso entre `DT_INTER` e a competência nos anos completos), e não de uma escolha arbitrária.
- **Corrigir o atraso por modelo (nowcasting).** Estima as internações ainda não faturadas, mas é um método estatístico que não está no plano de análise.

## Consequências

- A comparação perde o segundo semestre de 2023, 2024 e 2025. Os meses de julho a dezembro continuam descritos na série mensal, mas saem da comparação entre anos.
- Os meses comuns resolvem a diferença de calendário, mas não eliminam o atraso. Maio e junho de 2026 continuam incompletos. Falta decidir se a decisão vem acompanhada da exclusão dos meses mais recentes, com critério baseado no atraso observado.
- Com a aceitação, a decisão 0006 passou a ter status "Substituída em parte pela 0008", e o `CONTRIBUTING.md` voltou a descrever a regra dos meses comuns.
- No código, `meses_comuns` (`src/indicadores/_comum.py`) dá os meses cobertos por inteiro em todos os anos. `serie_anual_internacoes` e `serie_anual_todas_causas` calculam a razão de taxas só nesses meses e marcam o ano parcial na coluna `ano_parcial`. Os testes com valor feito à mão estão em `tests/indicadores/test_comum.py` e `tests/indicadores/test_internacoes.py`.
- A aplicação muda números já entregues. Ela exige teste com valor feito à mão e uma linha no `CHANGELOG.md`.

## Fonte

- Bittencourt, S. A.; Camacho, L. A. B.; Leal, M. C. O Sistema de Informação Hospitalar e sua aplicação na saúde coletiva. *Cadernos de Saúde Pública*, Rio de Janeiro, v. 22, n. 1, p. 19-30, 2006. Revisão sobre usos e limitações do SIH em pesquisa.
- Histórico do repositório: commit `5b4e403`, que removeu `_meses_comuns`.
