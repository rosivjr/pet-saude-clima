# 0010. Ponto fora do padrão de milhar interrompe a leitura do RESULTADO do SISAGUA

**Status:** Aceita
**Registro:** 2026-10-18

## Contexto

No SISAGUA, a coluna `RESULTADO` traz números em texto, com vírgula decimal ("0,15"), misturados a resultados qualitativos (PRESENTE ou AUSENTE). Até aqui, `converter_decimal_brasileiro` (`src/transformacoes.py`) apagava todo ponto como se fosse separador de milhar. Se a fonte passasse a gravar "0.5" com ponto decimal, o valor viraria 5 sem nenhum aviso: um cloro residual de 0,5 mg/L seria lido como 5 mg/L, e a conformidade com a Portaria GM/MS nº 888/2021 mudaria sem que ninguém percebesse.

Uma contagem feita em 18/10/2026, que mostrou só agregados e nenhum valor, leu os 6.539 valores de `RESULTADO` de Parauapebas em 2023-2026, todos preenchidos, nos seis parâmetros carregados. Nenhum tinha ponto, nem no padrão de milhar nem em forma ambígua. A regra abaixo, portanto, não muda nenhum resultado atual.

## Decisão

O ponto só é aceito como separador de milhar seguido de vírgula decimal, no padrão `PADRAO_MILHAR_BRASILEIRO` do `config.py` ("1.234,56", "-1.234,5"):

- qualquer outro valor com ponto ("0.5", "1.234", "<0.5") faz `converter_decimal_brasileiro` lançar `ValueError`, e o pipeline para;
- a mensagem informa só quantos valores foram recusados, sem mostrar nenhum, para não expor registros individuais;
- "1.234" sem vírgula também para, porque pode ser mil duzentos e trinta e quatro ou um vírgula duzentos e trinta e quatro.

## Alternativas

- **Manter o ponto como milhar.** Funciona com os dados atuais, mas erra em silêncio se o formato mudar.
- **Recusar qualquer ponto.** É mais simples, mas recusa um formato brasileiro válido ("1.234,56"), que nenhuma regra impede a fonte de usar.
- **Adivinhar o separador pelo número de casas.** Erra justamente nos casos ambíguos, como "1.234".

## Consequências

- Se o SISAGUA mudar o formato, a análise para em vez de produzir números errados. Será preciso conferir a fonte e rever esta decisão antes de seguir.
- Os testes `TestFormatoDecimal` (`tests/test_transformacoes.py`) cobrem o ponto decimal, os casos ambíguos, a mensagem sem valores e o milhar aceito.
- Quando novos anos forem baixados, a contagem deve ser refeita: quantos valores de `RESULTADO` têm ponto, por parâmetro, separando os que seguem o padrão de milhar ("1.234,56") dos ambíguos ("0.5", "1.234", "<0.5"), só com contagens.

## Fonte

- Ministério da Saúde. Portaria GM/MS nº 888, de 4 de maio de 2021 (padrões de potabilidade aos quais os valores lidos são comparados).
- Contagem de pontos em `RESULTADO`, executada pelo responsável pelo projeto em 18/10/2026: 6.539 valores, nenhum com ponto.
