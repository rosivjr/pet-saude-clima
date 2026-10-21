"""Largura e formatação de números, intervalos, datas e títulos."""

LARGURA = 78


def numero(valor: float, casas: int = 1) -> str:
    """Formata número no padrão brasileiro (vírgula decimal)."""
    return f"{valor:.{casas}f}".replace(".", ",")


def milhar(valor: int) -> str:
    """Formata inteiro com ponto de milhar: 13015 vira '13.015'."""
    return f"{valor:,}".replace(",", ".")


def ic(inferior: float, superior: float, casas: int = 1) -> str:
    """Formata um intervalo de confiança: 'IC95% 1,2–3,4'."""
    return f"IC95% {numero(inferior, casas)}–{numero(superior, casas)}"


def data(d) -> str:
    """Formata data como DD/MM/AAAA."""
    return d.strftime("%d/%m/%Y")


def titulo(texto: str) -> str:
    """Formata um título de seção com separadores."""
    return f"\n{'=' * LARGURA}\n{texto}\n{'=' * LARGURA}"


def subtitulo(texto: str) -> str:
    """Formata um subtítulo de seção."""
    return f"\n{texto}\n{'-' * LARGURA}"


def extracao(extracao) -> str:
    """
    Data de extração de uma fonte, com a mesma regra no relatório e nas figuras.

    Args:
        extracao: proveniencia.Extracao (primeira, última, do_download) ou None.
            Com do_download falso, ao menos uma data é a de modificação do
            arquivo, que muda quando ele é copiado.
    """
    if extracao is None:
        return "data de extração não registrada"
    primeira, ultima, do_download = extracao
    datas = data(primeira) if primeira == ultima else f"{data(primeira)} a {data(ultima)}"
    if do_download:
        return f"extraído em {datas}" if primeira == ultima else f"extraído de {datas}"
    return f"{datas} (data do arquivo, não da extração)"
