# 0007. Padronização direta por idade na comparação com o Pará

**Status:** Rejeitada para o relatório principal (2026-10-20)
**Registro:** 2026-10-18

**Motivo da rejeição:** o relatório principal não compara taxas entre locais. Em 20/10/2026, nem o `relatorio.txt` nem o código de `src/relatorio/` mostravam taxa do Pará ou do Brasil ao lado da de Parauapebas. As comparações com o Brasil são de saneamento (SINISA), percentuais que não dependem da estrutura etária. As taxas do relatório são brutas, e a limitação está em `docs/metodos.md`, "Limitações".

## Contexto

Hoje a comparação de Parauapebas com o Pará aparece só na análise do Sivep-DDA (`exploracao/dda/completar_dda.py` e `exploracao/dda/comparar_periodo_dda.py`), e o plano prevê estendê-la às internações. A comparação é bruta. Parauapebas cresceu pela migração de trabalhadores para a mineração e tem estrutura etária diferente da do estado. Os agravos DRSAI, por sua vez, variam com a idade (ver seção 15 do relatório). Uma diferença bruta mistura o risco com a composição etária das duas populações.

O exemplo, citado em `docs/metodos.md` até 20/10/2026, é o relatório DDA, que compara 2,03 por 10 mil em Parauapebas com 15,97 no Pará sem padronizar. Os valores são os que o `metodos.md` citava; o arquivo do relatório DDA não está no repositório. Hoje não há nenhuma padronização no código.

## Decisão

A padronização não é aplicada, porque o relatório principal não compara taxas entre locais. Ela volta a valer se o relatório DDA ou outro documento comparar Parauapebas com o Pará ou com outro local. Nesse caso, a comparação usa taxas padronizadas por idade, pelo método direto:

- **faixas etárias:** as do config (`FAIXA_ETARIA_LIMITES` e `FAIXA_ETARIA_ROTULOS`);
- **populações por faixa de Parauapebas e do Pará:** Censo 2022, tabela 9514 do SIDRA ("População residente, por sexo, idade e forma de declaração da idade"). A tabela traz a idade simples e permite montar as faixas do config;
- **população padrão:** a do Brasil na mesma tabela;
- **taxa padronizada:** Σ (taxa específica da faixa × população padrão da faixa) / população padrão total, por 100 mil pessoas-ano.

Se faltarem os casos do Pará por faixa etária, a padronização direta não é possível. Nesse caso, a comparação fica registrada como limitação explícita no relatório, e a taxa aparece como bruta.

## Alternativas

- **Manter a comparação bruta.** É a situação atual. A diferença de estrutura etária fica sem tratamento e a comparação pode enganar.
- **Padronização indireta (razão de mortalidade ou morbidade padronizada).** Precisa só do total de casos de Parauapebas e das taxas por faixa do Pará. É útil com poucos casos, mas o resultado não é comparável entre municípios diferentes.
- **População do Pará como padrão.** Foi sugerida na revisão do relatório. Torna a taxa padronizada do Pará igual à bruta, mas fica menos comparável com outros estudos nacionais.

## Consequências

- O intervalo de confiança da taxa padronizada ainda não está definido no plano de análise. Antes de aplicar a decisão, o método precisa entrar em `docs/metodos.md`. Um candidato é o de Fay e Feuer (1997), baseado na distribuição gama e coerente com o IC exato de Poisson das taxas brutas.
- As taxas padronizadas não são taxas reais da população. Servem só para comparar, e o relatório precisa dizer isso.
- O Censo 2022 vira a estrutura etária de todos os anos do período. A estrutura de Parauapebas muda depressa, e isso deve constar nas limitações.
- O método entra em `src/estatistica.py` com teste de valor feito à mão, como toda função de cálculo nova. A tabela 9514 deve ser baixada com o registro de proveniência exigido pelo `CONTRIBUTING.md`.
- O exemplo do relatório DDA usa taxas por 10 mil. O resto do projeto usa por 100 mil, e a comparação deve ser feita na mesma escala.

## Fonte

- Instituto Brasileiro de Geografia e Estatística (IBGE). Censo Demográfico 2022, tabela 9514 do SIDRA. Disponível em: https://sidra.ibge.gov.br/tabela/9514.
- Fay, M. P.; Feuer, E. J. Confidence intervals for directly standardized rates: a method based on the gamma distribution. *Statistics in Medicine*, v. 16, n. 7, p. 791-801, 1997.
- Rothman, K. J.; Greenland, S.; Lash, T. L. *Modern Epidemiology*. 3. ed. Filadélfia: Lippincott Williams & Wilkins, 2008. Padronização direta e indireta.
