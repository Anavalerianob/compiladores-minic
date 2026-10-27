from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from scanner import analisar as analisar_lexico
from validacao import validar_requisicao

app = Flask(__name__)


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
    # resultado da analise e informado nos campos "sucesso" e "erros".
    # As analises sintatica e semantica serao implementadas nas proximas etapas.
    resultado = analisar_lexico(codigo)
    tokens = resultado["tokens"]
    erros = resultado["erros"]

    if erros:
        mensagem = (
            f"Análise léxica concluída com {len(erros)} erro(s) léxico(s) "
            f"e {len(tokens)} token(s) reconhecido(s)."
        )
    else:
        mensagem = f"Análise léxica concluída sem erros: {len(tokens)} token(s) reconhecido(s)."

    return jsonify(
        recebido=True,
        sucesso=not erros,
        mensagem=mensagem,
        linhas=len(codigo.splitlines()),
        caracteres=len(codigo),
        tokens=tokens,
        erros=erros,
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
