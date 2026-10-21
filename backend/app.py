from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

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

    # As analises lexica, sintatica e semantica serao implementadas nas proximas etapas.
    return jsonify(
        recebido=True,
        mensagem="Código recebido com sucesso.",
        linhas=len(codigo.splitlines()),
        caracteres=len(codigo),
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
