"""Testes da geração de código intermediário.

As referências foram escritas à mão a partir da AST e da definição do enunciado,
não copiadas da saída do gerador.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import analisar  # noqa: E402
from parser import analisar_sintaxe  # noqa: E402
from intermediario import gerar_intermediario  # noqa: E402


def ir(codigo):
    ast = analisar_sintaxe(analisar(codigo)["tokens"])["ast"]
    return gerar_intermediario(ast)


def textos(r):
    return [i["texto"] for i in r["tres_enderecos"]]


def triplas(r):
    return [(t["numero"], t["op"], t["arg1"], t["arg2"]) for t in r["triplas"]]


def quadruplas(r):
    return [(q["op"], q["arg1"], q["arg2"], q["resultado"]) for q in r["quadruplas"]]


def ids_da_ast(no, saida=None):
    if saida is None:
        saida = set()
    saida.add(no["id"])
    for f in no["filhos"]:
        ids_da_ast(f, saida)
    return saida


REFERENCIA = "x = a + b * c - d;\ny = x / e;"


# ----------------------------------------------------------------------
# Referência obrigatória do enunciado
# ----------------------------------------------------------------------

def test_referencia_tres_enderecos():
    assert textos(ir(REFERENCIA)) == [
        "_t1 = b * c",
        "_t2 = a + _t1",
        "_t3 = _t2 - d",
        "x = _t3",
        "_t4 = x / e",
        "y = _t4",
    ]


def test_referencia_triplas():
    assert triplas(ir(REFERENCIA)) == [
        (1, "*", "b", "c"),
        (2, "+", "a", "(1)"),
        (3, "-", "(2)", "d"),
        (4, "=", "x", "(3)"),
        (5, "/", "x", "e"),
        (6, "=", "y", "(5)"),
    ]


def test_referencia_quadruplas():
    assert quadruplas(ir(REFERENCIA)) == [
        ("*", "b", "c", "_t1"),
        ("+", "a", "_t1", "_t2"),
        ("-", "_t2", "d", "_t3"),
        ("=", "_t3", None, "x"),
        ("/", "x", "e", "_t4"),
        ("=", "_t4", None, "y"),
    ]


def test_tres_listas_mesmo_tamanho():
    r = ir(REFERENCIA)
    assert len(r["tres_enderecos"]) == len(r["quadruplas"]) == len(r["triplas"]) == 6


# ----------------------------------------------------------------------
# Declarações
# ----------------------------------------------------------------------

def test_declaracao_com_literal_direto():
    assert textos(ir("int x = 5;")) == ["x = 5"]
    assert quadruplas(ir("int x = 5;")) == [("=", "5", None, "x")]
    assert triplas(ir("int x = 5;")) == [(1, "=", "x", "5")]


def test_declaracao_com_expressao():
    assert textos(ir("int y = a + 1;")) == ["_t1 = a + 1", "y = _t1"]


def test_declaracao_sem_inicializacao_nao_gera_instrucao():
    assert textos(ir("int x;")) == []
    assert textos(ir("int a; int b = 2;")) == ["b = 2"]


def test_lista_de_declaradores():
    # "int a, b = 2;" gera dois nós; só o segundo tem inicialização.
    assert textos(ir("int a, b = 2;")) == ["b = 2"]


# ----------------------------------------------------------------------
# Menos unário
# ----------------------------------------------------------------------

def test_menos_unario():
    assert textos(ir("x = -a * 2;")) == ["_t1 = minus a", "_t2 = _t1 * 2", "x = _t2"]
    assert triplas(ir("x = -a * 2;")) == [
        (1, "minus", "a", None),
        (2, "*", "(1)", "2"),
        (3, "=", "x", "(2)"),
    ]


# ----------------------------------------------------------------------
# Condicionais
# ----------------------------------------------------------------------

def test_if_com_else():
    r = ir("if (a < b) { x = 1; } else { x = 2; }")
    assert textos(r) == [
        "_t1 = a < b",
        "if_false _t1 goto L1",
        "x = 1",
        "goto L2",
        "label L1",
        "x = 2",
        "label L2",
    ]
    # Os desvios apontam para o número da instrução do rótulo de destino.
    assert triplas(r) == [
        (1, "<", "a", "b"),
        (2, "if_false", "(1)", 5),
        (3, "=", "x", "1"),
        (4, "goto", 7, None),
        (5, "label", "L1", None),
        (6, "=", "x", "2"),
        (7, "label", "L2", None),
    ]


def test_if_sem_else_nao_gera_goto():
    r = ir("if (a < b) { x = 1; }")
    assert textos(r) == [
        "_t1 = a < b",
        "if_false _t1 goto L1",
        "x = 1",
        "label L1",
    ]
    assert triplas(r)[1] == (2, "if_false", "(1)", 4)


def test_else_if_usa_rotulos_sequenciais():
    r = ir("if (a < b) { x = 1; } else if (c > d) { x = 2; } else { x = 3; }")
    assert textos(r) == [
        "_t1 = a < b",
        "if_false _t1 goto L1",
        "x = 1",
        "goto L2",
        "label L1",
        "_t2 = c > d",
        "if_false _t2 goto L3",
        "x = 2",
        "goto L4",
        "label L3",
        "x = 3",
        "label L4",
        "label L2",
    ]


# ----------------------------------------------------------------------
# Bordas e integração
# ----------------------------------------------------------------------

def test_programa_vazio():
    r = ir("")
    assert r == {"tres_enderecos": [], "quadruplas": [], "triplas": []}


def test_so_comentarios():
    assert textos(ir("// nada\n/* nada */")) == []


def test_cada_instrucao_referencia_um_no_da_ast():
    codigo = REFERENCIA
    ast = analisar_sintaxe(analisar(codigo)["tokens"])["ast"]
    r = gerar_intermediario(ast)
    ids = ids_da_ast(ast)
    for forma in (r["tres_enderecos"], r["quadruplas"], r["triplas"]):
        for instrucao in forma:
            assert instrucao["no"] in ids
    # A cópia "x = _t3" deve apontar para o nó da ATRIBUICAO de x.
    atribuicao_x = ast["filhos"][0]
    assert atribuicao_x["tipo"] == "ATRIBUICAO"
    assert r["tres_enderecos"][3]["no"] == atribuicao_x["id"]
