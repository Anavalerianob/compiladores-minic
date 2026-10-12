from flask import Flask, jsonify

app = Flask(__name__)


@app.after_request
def cors(resposta):
    resposta.headers["Access-Control-Allow-Origin"] = "*"
    return resposta


@app.get("/hello")
def hello():
    return jsonify(mensagem="Hello, World!")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
