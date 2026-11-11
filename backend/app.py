from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from scanner import analisar as analisar_lexico
from parser import analisar_sintaxe
from validacao import validar_requisicao

app = Flask(__name__)

MOTIVO_SEM_SINTATICO = (
    "A análise sintática não foi executada porque há erros léxicos. "
    "Corrija-os e analise novamente."
)


def _contar_nos(no):
    """Conta os nos da AST (incluindo a raiz)."""
    if no is None:
        return 0
    return 1 + sum(_contar_nos(filho) for filho in no["filhos"])


@app.get("/api/hello")
def hello():
    return jsonify(mensagem="Hello, World!")


@app.get("/api/saude")
def saude():
    return jsonify(status="ok")


@app.post("/api/analisar")
def analisar():
    dados = request.get_json(silent=True)
    codigo, erro = validar_requisicao(dados)

    if erro:
        return jsonify(recebido=False, erro=erro), 400

    # Erros lexicos nao alteram o status HTTP: a requisicao foi processada e o
    # resultado da analise e informado nos campos de cada etapa. A analise
    # semantica sera implementada na etapa 5.
    resultado = analisar_lexico(codigo)
    tokens = resultado["tokens"]
    erros = resultado["erros"]

    lexico = {"sucesso": not erros, "tokens": tokens, "erros": erros}

    if erros:
        # Com erros lexicos, o parser nao e executado: tokens faltando gerariam
        # erros sintaticos sem sentido.
        sintatico = {
            "executado": False,
            "sucesso": False,
            "ast": None,
            "erros": [],
            "motivo": MOTIVO_SEM_SINTATICO,
        }
        mensagem = (
            f"Análise léxica concluída com {len(erros)} erro(s) léxico(s) "
            f"e {len(tokens)} token(s) reconhecido(s). A análise sintática não foi executada."
        )
    else:
        analise = analisar_sintaxe(tokens)
        sintatico = {
            "executado": True,
            "sucesso": analise["sucesso"],
            "ast": analise["ast"],
            "erros": analise["erros"],
        }
        if analise["sucesso"]:
            nos = _contar_nos(analise["ast"])
            mensagem = (
                "Análise léxica e sintática concluídas sem erros: "
                f"{len(tokens)} token(s) e {nos} nó(s) na AST."
            )
        else:
            mensagem = (
                "Análise léxica sem erros; análise sintática com "
                f"{len(analise['erros'])} erro(s)."
            )

    return jsonify(
        recebido=True,
        sucesso=not erros,
        mensagem=mensagem,
        linhas=len(codigo.splitlines()),
        caracteres=len(codigo),
        tokens=tokens,
        erros=erros,
        lexico=lexico,
        sintatico=sintatico,
    ), 200


@app.errorhandler(404)
def nao_encontrado(_erro):
    return jsonify(erro="Recurso não encontrado."), 404


@app.errorhandler(405)
def metodo_nao_permitido(_erro):
    return jsonify(erro="Método não permitido para este recurso."), 405


@app.errorhandler(Exception)
def erro_inesperado(erro):
    if isinstance(erro, HTTPException):
        return jsonify(erro="Requisição inválida."), erro.code
    return jsonify(erro="Ocorreu um erro inesperado no servidor."), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
