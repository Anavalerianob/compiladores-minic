"""Validacoes iniciais do codigo-fonte recebido pela API."""

TAMANHO_MAXIMO = 10000


def validar_requisicao(dados):
    """Retorna (codigo, None) se a entrada for valida ou (None, mensagem_de_erro) caso contrario."""
    if not isinstance(dados, dict):
        return None, "Requisição inválida: envie um objeto JSON com o campo 'codigo'."

    if "codigo" not in dados:
        return None, "Requisição inválida: o campo 'codigo' é obrigatório."

    codigo = dados["codigo"]

    if not isinstance(codigo, str):
        return None, "Requisição inválida: o campo 'codigo' deve ser um texto."

    if codigo == "":
        return None, "Informe um código-fonte antes de solicitar a análise."

    if codigo.strip() == "":
        return None, "O código informado contém apenas espaços em branco. Escreva um programa antes de solicitar a análise."

    if len(codigo) > TAMANHO_MAXIMO:
        return None, f"O código excede o limite de {TAMANHO_MAXIMO} caracteres."

    return codigo, None
