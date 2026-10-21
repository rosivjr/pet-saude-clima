# 0005. Ligação da amostra ao cadastro pelo ano da coleta

**Status:** Aceita
**Registro:** 2026-10-18

## Contexto

O SISAGUA tem dois arquivos que precisam ser ligados. O de vigilância da qualidade traz uma linha por amostra, com o resultado medido. O de cadastro traz uma linha por solução de abastecimento e ano, com as características declaradas: tipo da solução, origem da captação e se faz desinfecção. A chave comum é `NU_SOLUCAO_ABASTECIMENTO`.

Uma solução pode mudar de um ano para outro (por exemplo, passar a desinfetar a água), e nem toda solução tem cadastro em todos os anos. A ligação precisa dizer de qual ano vem a característica atribuída a cada amostra.

## Decisão

`ligar_cadastro_por_ano` (`src/indicadores/abastecimento.py`) liga cada amostra ao cadastro da mesma solução nesta ordem:

1. cadastro do mesmo ano da coleta;
2. se não houver, cadastro do ano anterior mais próximo;
3. se não houver nenhum anterior, cadastro do ano seguinte mais próximo;
4. se a solução não tiver cadastro em nenhum ano, a amostra fica sem par, com as colunas do cadastro vazias.

Antes da ligação, a função confere que o par (solução, ano) não se repete no cadastro. Se repetir, ela lança `ValueError` e informa só quantas linhas se repetem, porque o `merge_asof` escolheria uma das linhas sem avisar.

O ano anterior tem preferência mesmo quando o seguinte está mais perto. Por exemplo, uma amostra de 2025 com cadastros de 2023 e 2026 é ligada ao de 2023. A função conta as amostras em cada caso (mesmo ano, ano anterior, ano seguinte, sem par) e o número de soluções sem par, grava as contagens em `resultado.attrs["ligacao"]` e as escreve no log, com um aviso quando há amostras sem par.

A ligação é usada em `ecoli_por_captacao` (amostras com *E. coli* presente por origem da captação) e em `divergencia_desinfeccao` (cloro medido nas soluções que declaram desinfecção).

## Alternativas

- **Só o cadastro do mesmo ano, descartando a amostra sem par.** Garante que a característica é a do ano da coleta, mas perde as amostras de soluções sem cadastro naquele ano. A perda não seria aleatória, porque soluções menores e alternativas tendem a ter cadastro mais irregular.

## Consequências

- Uma amostra pode receber uma característica que a solução não tinha no ano da coleta, quando o cadastro usado é de outro ano. Essa limitação consta em `docs/metodos.md`, seção de limitações.
- O relatório deve informar quantas amostras usaram cadastro de outro ano, porque esse número mostra se a regra pesa no resultado. As duas análises que usam a ligação mostram as contagens:
  - nas amostras com *E. coli* presente por origem da captação, a seção 14 mostra as quatro contagens. Na extração de 18/10/2026, as 1.430 amostras ligadas usaram o cadastro do mesmo ano;
  - na divergência de desinfecção, `divergencia_desinfeccao` repassa as contagens na chave `ligacao` e a seção 12 as mostra (`src/relatorio/abastecimento.py`), desde 20/10/2026. Antes, iam só para o log. Na execução de 20/10/2026, as 1.071 amostras de cloro usaram o cadastro do mesmo ano.
- Como a regra gerou os números já entregues, mudar para a alternativa exige nova decisão, teste com valor feito à mão e uma linha no `CHANGELOG.md`.

## Fonte

- Ministério da Saúde. SISAGUA: dados abertos de vigilância da qualidade da água e de cadastro das formas de abastecimento (chave `NU_SOLUCAO_ABASTECIMENTO`).
- Benchimol, E. I. et al. (2015). RECORD statement, itens 6.3 e 12.3 (método de ligação entre bases e descrição da qualidade da ligação).
