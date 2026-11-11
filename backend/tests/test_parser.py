"""Testes do parser (analise sintatica e AST) do MiniC.

Os valores esperados vem da gramatica e do enunciado da etapa 4, conferidos a mao
(contando colunas caractere a caractere), nao da saida atual do parser.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import analisar  # noqa: E402
from parser import analisar_sintaxe, MAX_PROFUNDIDADE, MAX_ERROS  # noqa: E402


def analisar_codigo(codigo):
    tokens = analisar(codigo)["tokens"]
    return analisar_sintaxe(tokens)


def ast(codigo):
    resultado = analisar_codigo(codigo)
    assert resultado["sucesso"], resultado["erros"]
    return resultado["ast"]


def erros(codigo):
    return analisar_codigo(codigo)["erros"]


def simplificar(no):
    """Reduz um no a tipo, atributos, papel e filhos (para comparacao estrutural)."""
    return {
        "tipo": no["tipo"],
        "atributos": no["atributos"],
        "papel": no["papel"],
        "filhos": [simplificar(f) for f in no["filhos"]],
    }


def folha(tipo, atributos, papel):
    return {"tipo": tipo, "atributos": atributos, "papel": papel, "filhos": []}


def coletar(no, saida=None):
    if saida is None:
        saida = []
    saida.append(no)
    for f in no["filhos"]:
        coletar(f, saida)
    return saida


# ----------------------------------------------------------------------
# Construcoes validas
# ----------------------------------------------------------------------

def test_programa_vazio():
    resultado = analisar_codigo("")
    assert resultado["sucesso"] is True
    assert resultado["erros"] == []
    assert resultado["ast"]["tipo"] == "PROGRAMA"
    assert resultado["ast"]["filhos"] == []


def test_somente_comentarios():
    resultado = analisar_codigo("// um comentario\n/* outro */")
    assert resultado["sucesso"] is True
    assert resultado["ast"]["tipo"] == "PROGRAMA"
    assert resultado["ast"]["filhos"] == []


def test_declaracao_sem_inicializacao():
    raiz = ast("int x;")
    assert simplificar(raiz) == {
        "tipo": "PROGRAMA", "atributos": {}, "papel": None,
        "filhos": [folha("DECLARACAO_VARIAVEL", {"tipoDado": "int", "nome": "x"}, "item")],
    }


def test_declaracao_com_inicializacao():
    raiz = ast("int x = 5;")
    decl = raiz["filhos"][0]
    assert decl["atributos"] == {"tipoDado": "int", "nome": "x"}
    assert len(decl["filhos"]) == 1
    assert decl["filhos"][0]["tipo"] == "LITERAL_INTEIRO"
    assert decl["filhos"][0]["papel"] == "valor"


def test_lista_de_declaradores_gera_dois_nos():
    raiz = ast("int a, b = 2;")
    assert [f["tipo"] for f in raiz["filhos"]] == ["DECLARACAO_VARIAVEL", "DECLARACAO_VARIAVEL"]
    a, b = raiz["filhos"]
    assert a["atributos"] == {"tipoDado": "int", "nome": "a"}
    assert a["filhos"] == []
    assert b["atributos"] == {"tipoDado": "int", "nome": "b"}
    assert b["filhos"][0]["tipo"] == "LITERAL_INTEIRO"
    # "int a" vai do "int" (tok 0) ate "a" (tok 1); "b = 2" vai de "b" (tok 3) a 2 (tok 5).
    assert (a["tokenInicio"], a["tokenFim"]) == (0, 1)
    assert (b["tokenInicio"], b["tokenFim"]) == (3, 5)


def test_float_com_literal_real():
    raiz = ast("float y = 3.5;")
    decl = raiz["filhos"][0]
    assert decl["atributos"] == {"tipoDado": "float", "nome": "y"}
    assert decl["filhos"][0]["tipo"] == "LITERAL_REAL"
    assert decl["filhos"][0]["atributos"] == {"valor": "3.5"}


def test_atribuicao():
    raiz = ast("x = 1;")
    atrib = raiz["filhos"][0]
    assert atrib["tipo"] == "ATRIBUICAO"
    assert atrib["atributos"] == {"nome": "x"}
    assert atrib["filhos"][0]["papel"] == "valor"


def test_comando_unico():
    raiz = ast("x = a + 1;")
    assert len(raiz["filhos"]) == 1
    assert raiz["filhos"][0]["tipo"] == "ATRIBUICAO"


def test_if_sem_else():
    raiz = ast("if (x > 0) { y = 1; }")
    cond = raiz["filhos"][0]
    assert cond["tipo"] == "CONDICIONAL"
    assert cond["atributos"] == {"temSenao": False}
    papeis = [f["papel"] for f in cond["filhos"]]
    assert papeis == ["condicao", "entao"]


def test_if_com_else():
    raiz = ast("if (x > 0) { y = 1; } else { y = 2; }")
    cond = raiz["filhos"][0]
    assert cond["atributos"] == {"temSenao": True}
    papeis = [f["papel"] for f in cond["filhos"]]
    assert papeis == ["condicao", "entao", "senao"]
    assert cond["filhos"][2]["tipo"] == "BLOCO"


def test_else_if():
    raiz = ast("if (a <= b) { a = 1; } else if (a > 0) { b = 2; } else { b = 3; }")
    externo = raiz["filhos"][0]
    assert externo["tipo"] == "CONDICIONAL"
    senao = externo["filhos"][2]
    assert senao["papel"] == "senao"
    assert senao["tipo"] == "CONDICIONAL"
    # CONDICIONAL(COMPARACAO, BLOCO, CONDICIONAL(COMPARACAO, BLOCO, BLOCO))
    assert [f["tipo"] for f in externo["filhos"]] == ["COMPARACAO", "BLOCO", "CONDICIONAL"]
    assert [f["tipo"] for f in senao["filhos"]] == ["COMPARACAO", "BLOCO", "BLOCO"]


def test_bloco_vazio():
    raiz = ast("if (x > 0) { }")
    bloco = raiz["filhos"][0]["filhos"][1]
    assert bloco["tipo"] == "BLOCO"
    assert bloco["filhos"] == []


def test_blocos_aninhados():
    raiz = ast("if (a > 0) { if (b > 0) { c = 1; } }")
    externo = raiz["filhos"][0]
    bloco_externo = externo["filhos"][1]
    assert bloco_externo["filhos"][0]["tipo"] == "CONDICIONAL"


# ----------------------------------------------------------------------
# Estrutura completa das referencias da secao 3.3
# ----------------------------------------------------------------------

def test_estrutura_referencia_precedencia():
    raiz = ast("int resultado = 10 + 5 * 2;")
    esperado = {
        "tipo": "PROGRAMA", "atributos": {}, "papel": None,
        "filhos": [{
            "tipo": "DECLARACAO_VARIAVEL",
            "atributos": {"tipoDado": "int", "nome": "resultado"}, "papel": "item",
            "filhos": [{
                "tipo": "ADICAO", "atributos": {"operador": "+"}, "papel": "valor",
                "filhos": [
                    folha("LITERAL_INTEIRO", {"valor": "10"}, "esquerda"),
                    {
                        "tipo": "MULTIPLICACAO", "atributos": {"operador": "*"}, "papel": "direita",
                        "filhos": [
                            folha("LITERAL_INTEIRO", {"valor": "5"}, "esquerda"),
                            folha("LITERAL_INTEIRO", {"valor": "2"}, "direita"),
                        ],
                    },
                ],
            }],
        }],
    }
    assert simplificar(raiz) == esperado


def test_estrutura_subtracao_associatividade():
    # 20 - 5 - 3  ->  SUBTRACAO(SUBTRACAO(20, 5), 3)
    raiz = ast("int r = 20 - 5 - 3;")
    sub = raiz["filhos"][0]["filhos"][0]
    assert sub["tipo"] == "SUBTRACAO"
    assert sub["filhos"][0]["tipo"] == "SUBTRACAO"
    assert sub["filhos"][1]["atributos"] == {"valor": "3"}
    interno = sub["filhos"][0]
    assert interno["filhos"][0]["atributos"] == {"valor": "20"}
    assert interno["filhos"][1]["atributos"] == {"valor": "5"}


def test_estrutura_parenteses():
    # (10 + 5) * 2  ->  MULTIPLICACAO(ADICAO(10, 5), 2)
    raiz = ast("int r = (10 + 5) * 2;")
    mult = raiz["filhos"][0]["filhos"][0]
    assert mult["tipo"] == "MULTIPLICACAO"
    assert mult["filhos"][0]["tipo"] == "ADICAO"
    assert mult["filhos"][1]["atributos"] == {"valor": "2"}


def test_estrutura_negacao():
    # -a * 2  ->  MULTIPLICACAO(NEGACAO(a), 2)
    raiz = ast("x = -a * 2;")
    mult = raiz["filhos"][0]["filhos"][0]
    assert mult["tipo"] == "MULTIPLICACAO"
    neg = mult["filhos"][0]
    assert neg["tipo"] == "NEGACAO"
    assert neg["atributos"] == {"operador": "-"}
    assert neg["filhos"][0]["tipo"] == "IDENTIFICADOR"
    assert neg["filhos"][0]["papel"] == "operando"


def test_estrutura_condicional_encadeada():
    raiz = ast("if (a <= b) { a = 1; } else if (a > 0) { b = 2; } else { b = 3; }")
    externo = raiz["filhos"][0]
    assert externo["filhos"][0]["tipo"] == "COMPARACAO"
    assert externo["filhos"][0]["atributos"] == {"operador": "<="}
    assert externo["filhos"][2]["filhos"][0]["atributos"] == {"operador": ">"}


# ----------------------------------------------------------------------
# Precedencia e associatividade
# ----------------------------------------------------------------------

def test_precedencia_soma_multiplicacao():
    # 2 + 3 * 4  ->  ADICAO(2, MULTIPLICACAO(3, 4))
    raiz = ast("x = 2 + 3 * 4;")
    topo = raiz["filhos"][0]["filhos"][0]
    assert topo["tipo"] == "ADICAO"
    assert topo["filhos"][0]["atributos"] == {"valor": "2"}
    assert topo["filhos"][1]["tipo"] == "MULTIPLICACAO"


def test_associatividade_subtracao():
    raiz = ast("x = 10 - 3 - 2;")
    topo = raiz["filhos"][0]["filhos"][0]
    assert topo["tipo"] == "SUBTRACAO"
    assert topo["filhos"][0]["tipo"] == "SUBTRACAO"   # esquerda
    assert topo["filhos"][1]["atributos"] == {"valor": "2"}


def test_associatividade_divisao():
    # 8 / 4 / 2  ->  DIVISAO(DIVISAO(8, 4), 2)
    raiz = ast("x = 8 / 4 / 2;")
    topo = raiz["filhos"][0]["filhos"][0]
    assert topo["tipo"] == "DIVISAO"
    assert topo["filhos"][0]["tipo"] == "DIVISAO"
    assert topo["filhos"][0]["filhos"][0]["atributos"] == {"valor": "8"}
    assert topo["filhos"][1]["atributos"] == {"valor": "2"}


def test_menos_unario_duplo():
    # - - a  ->  NEGACAO(NEGACAO(a))
    raiz = ast("x = - - a;")
    topo = raiz["filhos"][0]["filhos"][0]
    assert topo["tipo"] == "NEGACAO"
    assert topo["filhos"][0]["tipo"] == "NEGACAO"
    assert topo["filhos"][0]["filhos"][0]["tipo"] == "IDENTIFICADOR"


def test_comparacao_entre_aditivas():
    # a + 1 < b  ->  COMPARACAO(ADICAO(a,1), b)
    raiz = ast("x = a + 1 < b;")
    topo = raiz["filhos"][0]["filhos"][0]
    assert topo["tipo"] == "COMPARACAO"
    assert topo["atributos"] == {"operador": "<"}
    assert topo["filhos"][0]["tipo"] == "ADICAO"
    assert topo["filhos"][1]["tipo"] == "IDENTIFICADOR"


# ----------------------------------------------------------------------
# Posicoes, ordem de criacao e ids
# ----------------------------------------------------------------------

def test_posicoes_referencia():
    raiz = ast("int resultado = 10 + 5 * 2;")
    decl = raiz["filhos"][0]
    adicao = decl["filhos"][0]
    lit10 = adicao["filhos"][0]
    mult = adicao["filhos"][1]
    lit5 = mult["filhos"][0]
    lit2 = mult["filhos"][1]

    assert (decl["linha"], decl["coluna"], decl["linhaFim"], decl["colunaFim"]) == (1, 1, 1, 27)
    assert (adicao["linha"], adicao["coluna"], adicao["linhaFim"], adicao["colunaFim"]) == (1, 17, 1, 26)
    assert (lit10["linha"], lit10["coluna"], lit10["linhaFim"], lit10["colunaFim"]) == (1, 17, 1, 18)
    assert (mult["linha"], mult["coluna"], mult["linhaFim"], mult["colunaFim"]) == (1, 22, 1, 26)
    assert (lit5["linha"], lit5["coluna"]) == (1, 22)
    assert (lit2["linha"], lit2["coluna"]) == (1, 26)


def test_tokens_inicio_fim_referencia():
    raiz = ast("int resultado = 10 + 5 * 2;")
    decl = raiz["filhos"][0]
    adicao = decl["filhos"][0]
    mult = adicao["filhos"][1]
    # tokens: int0 resultado1 =2 10:3 +4 5:5 *6 2:7 ;8
    assert (decl["tokenInicio"], decl["tokenFim"]) == (0, 8)
    assert (adicao["tokenInicio"], adicao["tokenFim"]) == (3, 7)
    assert (mult["tokenInicio"], mult["tokenFim"]) == (5, 7)


def test_ordem_de_criacao_referencia():
    raiz = ast("int resultado = 10 + 5 * 2;")
    nos = coletar(raiz)
    por_tipo_valor = {}
    for no in nos:
        chave = no["tipo"]
        if no["tipo"] == "LITERAL_INTEIRO":
            chave = "LIT" + no["atributos"]["valor"]
        por_tipo_valor[chave] = no["ordem"]
    # Ordem esperada: 10, 5, 2, MULTIPLICACAO, ADICAO, DECLARACAO_VARIAVEL, PROGRAMA
    assert por_tipo_valor["LIT10"] == 1
    assert por_tipo_valor["LIT5"] == 2
    assert por_tipo_valor["LIT2"] == 3
    assert por_tipo_valor["MULTIPLICACAO"] == 4
    assert por_tipo_valor["ADICAO"] == 5
    assert por_tipo_valor["DECLARACAO_VARIAVEL"] == 6
    assert por_tipo_valor["PROGRAMA"] == 7


def test_ids_unicos_e_iguais_a_ordem():
    raiz = ast("if (a <= b) { a = 1; } else if (a > 0) { b = 2; } else { b = 3; }")
    nos = coletar(raiz)
    ids = [no["id"] for no in nos]
    assert len(ids) == len(set(ids))
    for no in nos:
        assert no["id"] == no["ordem"]


# ----------------------------------------------------------------------
# Erros sintaticos (tabela da secao 3.4)
# ----------------------------------------------------------------------

def primeiro_erro(codigo):
    lista = erros(codigo)
    assert lista, "esperava ao menos um erro"
    return lista[0]


def test_erro_declaracao_sem_ponto_e_virgula_fim():
    e = primeiro_erro("int x = 5")
    assert e["encontrado"] == "fim do código"
    assert e["esperado"] == [";"]
    assert (e["linha"], e["coluna"]) == (1, 10)


def test_erro_declaracao_falta_ponto_e_virgula_antes_de_outra():
    e = primeiro_erro("int x = 5\nint y;")
    assert e["encontrado"] == "int"
    assert (e["linha"], e["coluna"]) == (2, 1)
    assert e["esperado"] == [";"]


def test_erro_if_sem_fechar_parentese():
    e = primeiro_erro("if (x > 0 { x = 1; }")
    assert e["encontrado"] == "{"
    assert e["esperado"] == [")"]
    assert "condição do if" in e["mensagem"]


def test_erro_bloco_nao_fechado():
    e = primeiro_erro("{ int a;")
    assert e["encontrado"] == "fim do código"
    assert e["esperado"] == ["}"]
    assert "linha 1" in e["mensagem"]


def test_erro_else_sem_if():
    e = primeiro_erro("else { x = 1; }")
    assert "else" in e["mensagem"]
    assert "if" in e["mensagem"]


def test_erro_operando_ausente_apos_operador():
    e = primeiro_erro("x = 1 + * 2;")
    assert e["encontrado"] == "*"
    assert e["esperado"] == ["IDENTIFICADOR", "LITERAL_INTEIRO", "LITERAL_REAL", "(", "-"]


def test_erro_palavra_reservada_como_nome():
    e = primeiro_erro("int if = 3;")
    assert e["encontrado"] == "if"
    assert "palavra reservada" in e["mensagem"]


def test_erro_expressao_sem_operando():
    e = primeiro_erro("x = ;")
    assert e["encontrado"] == ";"
    assert e["esperado"] == ["IDENTIFICADOR", "LITERAL_INTEIRO", "LITERAL_REAL", "(", "-"]


def test_erro_parentese_nao_fechado_na_expressao():
    e = primeiro_erro("int a = (1 + 2;")
    assert e["encontrado"] == ";"
    assert e["esperado"] == [")"]


def test_erro_comparacao_encadeada():
    e = primeiro_erro("if (a < b < c) { }")
    assert "encadeada" in e["mensagem"]


def test_erro_comando_comeca_com_numero():
    e = primeiro_erro("10 = x;")
    assert e["encontrado"] == "10"
    assert "número" in e["mensagem"]


def test_erro_chave_de_fechamento_sem_bloco():
    e = primeiro_erro("int x = 1; }")
    assert e["encontrado"] == "}"
    assert "fechamento" in e["mensagem"] or "bloco aberto" in e["mensagem"]


def test_erro_regra_e_citada():
    e = primeiro_erro("int x = 5")
    assert e["regra"] == 'declaracao = tipo declarador { "," declarador } ";"'


def test_erro_implica_ast_nula():
    resultado = analisar_codigo("int x = 5")
    assert resultado["sucesso"] is False
    assert resultado["ast"] is None


# ----------------------------------------------------------------------
# Recuperacao de erros (modo panico)
# ----------------------------------------------------------------------

def test_recuperacao_dois_erros_em_linhas_diferentes():
    lista = erros("int x = 5\nint y = ;\nint z = 6;")
    assert len(lista) == 2
    assert lista[0]["linha"] == 2   # falta ; de x, detectada no "int" da linha 2
    assert lista[1]["linha"] == 2   # operando ausente de y


def test_recuperacao_sem_cascata():
    # Um unico erro (operando ausente) nao deve gerar erros em cascata.
    lista = erros("x = 1 + * 2;")
    assert len(lista) == 1


def test_recuperacao_limite_de_erros():
    lista = erros("\n".join("int x = ;" for _ in range(40)))
    # 20 erros reais + 1 aviso de interrupcao.
    assert len(lista) == MAX_ERROS + 1
    assert "interrompida" in lista[-1]["mensagem"]


# ----------------------------------------------------------------------
# Limite de aninhamento
# ----------------------------------------------------------------------

def test_limite_de_aninhamento_nao_estoura():
    codigo = "x = " + "(" * 150 + "1" + ")" * 150 + ";"
    resultado = analisar_codigo(codigo)
    assert resultado["sucesso"] is False
    assert any(str(MAX_PROFUNDIDADE) in e["mensagem"] for e in resultado["erros"])


# ----------------------------------------------------------------------
# Integracao com o scanner
# ----------------------------------------------------------------------

def test_tokens_da_ast_correspondem_aos_lexemas():
    codigo = "int resultado = 10 + 5 * 2;"
    tokens = analisar(codigo)["tokens"]
    raiz = analisar_sintaxe(tokens)["ast"]
    for no in coletar(raiz):
        if no["tokenInicio"] is None:
            continue
        assert 0 <= no["tokenInicio"] <= no["tokenFim"] < len(tokens)
        # O primeiro token do no comeca na posicao registrada no proprio no.
        ti = tokens[no["tokenInicio"]]
        assert (ti["linha"], ti["coluna"]) == (no["linha"], no["coluna"])


def test_scanner_nao_e_alterado_pelo_parser():
    codigo = "int x = 1;"
    antes = analisar(codigo)["tokens"]
    copia = [dict(t) for t in antes]
    analisar_sintaxe(antes)
    assert antes == copia
