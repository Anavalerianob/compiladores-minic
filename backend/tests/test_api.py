import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as modulo_app  # noqa: E402
from validacao import TAMANHO_MAXIMO, validar_requisicao  # noqa: E402


@pytest.fixture
def cliente():
    modulo_app.app.config["TESTING"] = True
    return modulo_app.app.test_client()


# Testes unitarios da validacao

def test_validacao_aceita_codigo_valido():
    codigo, erro = validar_requisicao({"codigo": "int numero = 10;"})
    assert codigo == "int numero = 10;"
    assert erro is None


def test_validacao_rejeita_dados_que_nao_sao_objeto():
    codigo, erro = validar_requisicao(["int a;"])
    assert codigo is None
    assert "objeto JSON" in erro


def test_validacao_rejeita_campo_ausente():
    _, erro = validar_requisicao({})
    assert "obrigatório" in erro


def test_validacao_rejeita_codigo_que_nao_e_texto():
    _, erro = validar_requisicao({"codigo": 123})
    assert "texto" in erro


def test_validacao_rejeita_codigo_vazio():
    _, erro = validar_requisicao({"codigo": ""})
    assert erro == "Informe um código-fonte antes de solicitar a análise."


def test_validacao_rejeita_apenas_espacos():
    _, erro = validar_requisicao({"codigo": "   \n\t  "})
    assert "espaços em branco" in erro


def test_validacao_rejeita_codigo_muito_grande():
    _, erro = validar_requisicao({"codigo": "a" * (TAMANHO_MAXIMO + 1)})
    assert "limite" in erro


# Testes dos endpoints

def test_regressao_hello(cliente):
    resposta = cliente.get("/api/hello")
    assert resposta.status_code == 200
    assert resposta.get_json() == {"mensagem": "Hello, World!"}


def test_saude(cliente):
    resposta = cliente.get("/api/saude")
    assert resposta.status_code == 200
    assert resposta.get_json() == {"status": "ok"}


def test_analisar_codigo_valido(cliente):
    resposta = cliente.post("/api/analisar", json={"codigo": "int numero = 10;\nfloat b;"})
    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["recebido"] is True
    assert corpo["mensagem"] == "Código recebido com sucesso."
    assert corpo["linhas"] == 2
    assert corpo["caracteres"] == len("int numero = 10;\nfloat b;")


def test_analisar_aceita_codigo_com_erro_intencional(cliente):
    resposta = cliente.post("/api/analisar", json={"codigo": "int x = ;"})
    assert resposta.status_code == 200
    assert resposta.get_json()["recebido"] is True


def test_analisar_aceita_caracteres_especiais(cliente):
    codigo = '#include <stdio.h>\nprintf("%d\\n", 10); // ação é ç'
    resposta = cliente.post("/api/analisar", json={"codigo": codigo})
    assert resposta.status_code == 200
    assert resposta.get_json()["caracteres"] == len(codigo)


def test_analisar_codigo_vazio(cliente):
    resposta = cliente.post("/api/analisar", json={"codigo": ""})
    assert resposta.status_code == 400
    corpo = resposta.get_json()
    assert corpo["recebido"] is False
    assert corpo["erro"] == "Informe um código-fonte antes de solicitar a análise."


def test_analisar_apenas_espacos(cliente):
    resposta = cliente.post("/api/analisar", json={"codigo": "     "})
    assert resposta.status_code == 400
    assert "espaços em branco" in resposta.get_json()["erro"]


def test_analisar_sem_campo_codigo(cliente):
    resposta = cliente.post("/api/analisar", json={"texto": "int a;"})
    assert resposta.status_code == 400
    assert "obrigatório" in resposta.get_json()["erro"]


def test_analisar_campo_com_tipo_errado(cliente):
    resposta = cliente.post("/api/analisar", json={"codigo": ["int a;"]})
    assert resposta.status_code == 400


def test_analisar_corpo_que_nao_e_json(cliente):
    resposta = cliente.post("/api/analisar", data="int a;", content_type="text/plain")
    assert resposta.status_code == 400
    assert resposta.get_json()["recebido"] is False


def test_analisar_json_malformado(cliente):
    resposta = cliente.post("/api/analisar", data="{codigo:", content_type="application/json")
    assert resposta.status_code == 400


def test_analisar_metodo_get_nao_permitido(cliente):
    resposta = cliente.get("/api/analisar")
    assert resposta.status_code == 405
    assert "erro" in resposta.get_json()


def test_rota_inexistente(cliente):
    resposta = cliente.get("/api/nao-existe")
    assert resposta.status_code == 404
    assert resposta.get_json() == {"erro": "Recurso não encontrado."}


def test_erro_inesperado_nao_expoe_detalhes(cliente, monkeypatch):
    def falhar(_dados):
        raise RuntimeError("segredo interno /app/validacao.py")

    monkeypatch.setattr(modulo_app, "validar_requisicao", falhar)
    resposta = cliente.post("/api/analisar", json={"codigo": "int a;"})
    assert resposta.status_code == 500
    texto = resposta.get_data(as_text=True)
    assert "segredo" not in texto
    assert "Traceback" not in texto
    assert resposta.get_json() == {"erro": "Ocorreu um erro inesperado no servidor."}
