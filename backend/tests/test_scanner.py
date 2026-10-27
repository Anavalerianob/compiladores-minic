import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import PALAVRAS_RESERVADAS, analisar  # noqa: E402


def tokens(codigo):
    return analisar(codigo)["tokens"]


def erros(codigo):
    return analisar(codigo)["erros"]


def pares(codigo):
    """Lista (tipo, lexema) dos tokens reconhecidos."""
    return [(t["tipo"], t["lexema"]) for t in tokens(codigo)]


def posicoes(codigo):
    """Lista (lexema, linha, coluna) dos tokens reconhecidos."""
    return [(t["lexema"], t["linha"], t["coluna"]) for t in tokens(codigo)]


# Palavras reservadas

@pytest.mark.parametrize("palavra", PALAVRAS_RESERVADAS)
def test_palavra_reservada(palavra):
    assert pares(palavra) == [("PALAVRA_RESERVADA", palavra)]
    assert erros(palavra) == []


def test_palavras_reservadas_do_subconjunto():
    assert set(PALAVRAS_RESERVADAS) == {"int", "float", "if", "else"}


@pytest.mark.parametrize("lexema", ["INT", "Float", "IF", "Else"])
def test_palavra_reservada_e_sensivel_a_maiusculas(lexema):
    assert pares(lexema) == [("IDENTIFICADOR", lexema)]


@pytest.mark.parametrize("lexema", ["integer", "iff", "floats", "elsewhere", "int1"])
def test_prefixo_de_palavra_reservada_e_identificador(lexema):
    assert pares(lexema) == [("IDENTIFICADOR", lexema)]


# Identificadores

@pytest.mark.parametrize("lexema", ["numero", "_x1", "a", "resultado_final", "X2y3", "__"])
def test_identificador_valido(lexema):
    assert pares(lexema) == [("IDENTIFICADOR", lexema)]
    assert erros(lexema) == []


def test_identificador_iniciado_por_digito_gera_erro():
    resultado = analisar("1abc")
    assert resultado["tokens"] == []
    assert len(resultado["erros"]) == 1
    assert resultado["erros"][0]["lexema"] == "1abc"


def test_letras_acentuadas_geram_erro():
    resultado = analisar("ação")
    assert [(t["lexema"], t["coluna"]) for t in resultado["tokens"]] == [("a", 1), ("o", 4)]
    assert [(e["lexema"], e["coluna"]) for e in resultado["erros"]] == [("ç", 2), ("ã", 3)]


# Literais numericos

@pytest.mark.parametrize("lexema", ["0", "10", "42", "007"])
def test_literal_inteiro(lexema):
    assert pares(lexema) == [("LITERAL_INTEIRO", lexema)]


@pytest.mark.parametrize("lexema", ["3.5", "0.25", "10.0"])
def test_literal_real(lexema):
    assert pares(lexema) == [("LITERAL_REAL", lexema)]


@pytest.mark.parametrize("trecho", ["3.", "3.5.2", "12abc", "1.2x"])
def test_literal_malformado(trecho):
    resultado = analisar(trecho)
    assert resultado["tokens"] == []
    assert len(resultado["erros"]) == 1
    erro = resultado["erros"][0]
    assert erro["lexema"] == trecho
    assert (erro["linha"], erro["coluna"]) == (1, 1)
    assert f"literal numérico malformado '{trecho}'" in erro["mensagem"]


def test_literal_malformado_nao_interrompe_a_analise():
    resultado = analisar("float x = 3.;")
    assert pares("float x = 3.;") == [
        ("PALAVRA_RESERVADA", "float"), ("IDENTIFICADOR", "x"), ("OPERADOR", "="), ("DELIMITADOR", ";"),
    ]
    assert [e["lexema"] for e in resultado["erros"]] == ["3."]


def test_ponto_antes_do_numero_gera_erro_e_inteiro():
    resultado = analisar(".5")
    assert [(e["lexema"], e["coluna"]) for e in resultado["erros"]] == [(".", 1)]
    assert [(t["tipo"], t["lexema"], t["coluna"]) for t in resultado["tokens"]] == [("LITERAL_INTEIRO", "5", 2)]


# Operadores

@pytest.mark.parametrize("operador", ["+", "-", "*", "/", "=", "==", "!=", "<", "<=", ">", ">="])
def test_operador(operador):
    assert pares(operador) == [("OPERADOR", operador)]
    assert erros(operador) == []


def test_operadores_compostos_pelo_maior_lexema():
    assert pares("a<=b==c") == [
        ("IDENTIFICADOR", "a"), ("OPERADOR", "<="), ("IDENTIFICADOR", "b"),
        ("OPERADOR", "=="), ("IDENTIFICADOR", "c"),
    ]


def test_igual_separado_por_espaco_gera_dois_tokens():
    assert pares("= =") == [("OPERADOR", "="), ("OPERADOR", "=")]


def test_exclamacao_isolada_gera_erro_e_continua():
    resultado = analisar("!a")
    assert pares("!a") == [("IDENTIFICADOR", "a")]
    assert len(resultado["erros"]) == 1
    erro = resultado["erros"][0]
    assert (erro["lexema"], erro["linha"], erro["coluna"]) == ("!", 1, 1)
    assert "'!='" in erro["mensagem"]


# Delimitadores

@pytest.mark.parametrize("delimitador", ["(", ")", "{", "}", ";", ","])
def test_delimitador(delimitador):
    assert pares(delimitador) == [("DELIMITADOR", delimitador)]


# Comentarios e espacos

def test_comentario_de_linha_e_ignorado():
    resultado = analisar("int a; // comentario com @ e #\nfloat b;")
    assert resultado["erros"] == []
    assert [t["lexema"] for t in resultado["tokens"]] == ["int", "a", ";", "float", "b", ";"]
    assert (resultado["tokens"][3]["linha"], resultado["tokens"][3]["coluna"]) == (2, 1)


def test_comentario_de_bloco_com_varias_linhas():
    resultado = analisar("/* linha 1\n linha 2 */ int")
    assert resultado["erros"] == []
    assert posicoes("/* linha 1\n linha 2 */ int") == [("int", 2, 13)]


def test_comentario_de_bloco_nao_fechado():
    resultado = analisar("int a;\n  /* sem fim\nint b;")
    assert [t["lexema"] for t in resultado["tokens"]] == ["int", "a", ";"]
    assert len(resultado["erros"]) == 1
    erro = resultado["erros"][0]
    assert (erro["lexema"], erro["linha"], erro["coluna"]) == ("/*", 2, 3)
    assert "*/" in erro["mensagem"]


def test_espacos_tabulacoes_e_quebras_nao_geram_tokens():
    assert analisar(" \t\r\n  \n\t") == {"tokens": [], "erros": []}


def test_tabulacao_conta_como_uma_coluna():
    assert posicoes("\tint") == [("int", 1, 2)]


def test_quebra_de_linha_windows():
    assert posicoes("int\r\nfloat") == [("int", 1, 1), ("float", 2, 1)]


# Linha e coluna

def test_linha_e_coluna_de_todos_os_tokens():
    assert posicoes("int numero = 10;\n  if (numero > 0)") == [
        ("int", 1, 1), ("numero", 1, 5), ("=", 1, 12), ("10", 1, 14), (";", 1, 16),
        ("if", 2, 3), ("(", 2, 6), ("numero", 2, 7), (">", 2, 14), ("0", 2, 16), (")", 2, 17),
    ]


# Erros

def test_erro_com_dicionario_completo():
    assert erros("a @") == [{
        "tipo": "ERRO_LEXICO",
        "lexema": "@",
        "linha": 1,
        "coluna": 3,
        "mensagem": "Erro léxico na linha 1, coluna 3: caractere não reconhecido '@'. "
                    "Verifique se ele faz parte do subconjunto suportado.",
    }]


def test_erros_sao_acumulados():
    resultado = analisar("a @ b # c $")
    assert [t["lexema"] for t in resultado["tokens"]] == ["a", "b", "c"]
    assert [(e["lexema"], e["coluna"]) for e in resultado["erros"]] == [("@", 3), ("#", 7), ("$", 11)]


@pytest.mark.parametrize("caractere", ['"', "'", "&", "|"])
def test_caracteres_fora_do_escopo(caractere):
    resultado = analisar(caractere)
    assert resultado["tokens"] == []
    assert resultado["erros"][0]["lexema"] == caractere


def test_codigo_sintaticamente_errado_e_tokenizado_sem_erro():
    resultado = analisar("int = = ; if else )")
    assert resultado["erros"] == []
    assert pares("int = = ; if else )") == [
        ("PALAVRA_RESERVADA", "int"), ("OPERADOR", "="), ("OPERADOR", "="), ("DELIMITADOR", ";"),
        ("PALAVRA_RESERVADA", "if"), ("PALAVRA_RESERVADA", "else"), ("DELIMITADOR", ")"),
    ]


# Bordas

def test_codigo_vazio():
    assert analisar("") == {"tokens": [], "erros": []}


def test_apenas_comentarios():
    assert analisar("// linha\n/* bloco */") == {"tokens": [], "erros": []}


def test_token_no_fim_sem_quebra_de_linha():
    assert posicoes("int a = 5") == [("int", 1, 1), ("a", 1, 5), ("=", 1, 7), ("5", 1, 9)]


def test_barra_no_fim_do_arquivo():
    assert posicoes("a /") == [("a", 1, 1), ("/", 1, 3)]
    assert erros("a /") == []


# Transicoes do automato

def test_transicoes_de_identificador():
    assert tokens("ab")[0]["transicoes"] == [
        {"de": "inicial", "caractere": "a", "para": "identificador"},
        {"de": "identificador", "caractere": "b", "para": "identificador"},
    ]


def test_transicoes_de_literal_real():
    assert tokens("3.5")[0]["transicoes"] == [
        {"de": "inicial", "caractere": "3", "para": "inteiro"},
        {"de": "inteiro", "caractere": ".", "para": "ponto_decimal"},
        {"de": "ponto_decimal", "caractere": "5", "para": "real"},
    ]


def test_transicoes_de_operador_composto():
    assert tokens("<=")[0]["transicoes"] == [
        {"de": "inicial", "caractere": "<", "para": "menor"},
        {"de": "menor", "caractere": "=", "para": "operador"},
    ]


def test_todo_token_tem_as_chaves_do_contrato():
    for token in tokens("int a = (1 + 2.5) / 3;"):
        assert set(token) == {"tipo", "lexema", "linha", "coluna", "transicoes"}
        assert "".join(t["caractere"] for t in token["transicoes"]) == token["lexema"]
