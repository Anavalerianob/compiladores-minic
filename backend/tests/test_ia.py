"""Testes da explicação com IA (Ollama), com a chamada HTTP substituída por monkeypatch.

Nenhum teste aqui fala com o Ollama de verdade. O teste de integração real fica no
fim e é pulado a menos que OLLAMA_INTEGRACAO=1.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ia  # noqa: E402
import app as modulo_app  # noqa: E402

CODIGO_REF = "int resultado = 10 + 5 * 2;"


@pytest.fixture
def cliente():
    modulo_app.app.config["TESTING"] = True
    return modulo_app.app.test_client()


def fake_ok(registro=None, conteudo="Explicação do professor virtual.", modelo="llama3.2"):
    """Substituto de _post_json: /api/tags lista o modelo; /api/chat responde conteudo."""
    def _post(url, dados, timeout):
        if url.endswith("/api/tags"):
            return {"models": [{"name": modelo + ":latest"}]}
        if registro is not None:
            registro["url"] = url
            registro["dados"] = dados
        return {"message": {"content": conteudo}}
    return _post


def fake_chat(resposta_chat, modelo="llama3.2"):
    def _post(url, dados, timeout):
        if url.endswith("/api/tags"):
            return {"models": [{"name": modelo}]}
        return resposta_chat()
    return _post


def fake_falha_chat(excecao, registro):
    def _post(url, dados, timeout):
        if url.endswith("/api/tags"):
            return {"models": [{"name": "llama3.2"}]}
        registro["chat"] = registro.get("chat", 0) + 1
        raise excecao
    return _post


# ----------------------------------------------------------------------
# Caminho feliz e montagem do contexto
# ----------------------------------------------------------------------

def test_extrai_conteudo_da_resposta(monkeypatch):
    registro = {}
    monkeypatch.setattr(ia, "_post_json", fake_ok(registro))
    status, corpo = ia.gerar_explicacao("PERGUNTA", "int x = 1;", None, "O que é um token?")
    assert status == 200
    assert corpo["explicacao"] == "Explicação do professor virtual."
    assert corpo["modelo"] == "llama3.2"
    assert corpo["geradoPorIA"] is True


def test_contexto_tem_sistema_e_codigo_entre_dados(monkeypatch):
    registro = {}
    monkeypatch.setattr(ia, "_post_json", fake_ok(registro))
    ia.gerar_explicacao("PERGUNTA", CODIGO_REF, None, "Explique a precedência.")
    mensagens = registro["dados"]["messages"]
    assert mensagens[0]["role"] == "system"
    assert "professor de Compiladores" in mensagens[0]["content"]
    usuario = mensagens[1]["content"]
    assert "<dados>" in usuario and "</dados>" in usuario
    assert CODIGO_REF in usuario
    assert usuario.index("<dados>") < usuario.index(CODIGO_REF) < usuario.index("</dados>")


def test_contexto_no_tem_no_pai_filhos_e_regra(monkeypatch):
    registro = {}
    monkeypatch.setattr(ia, "_post_json", fake_ok(registro))
    # Em "int resultado = 10 + 5 * 2;" o nó de id 4 é a MULTIPLICACAO (ordem 4).
    status, _ = ia.gerar_explicacao("NO_AST", CODIGO_REF, 4, None)
    assert status == 200
    conteudo = registro["dados"]["messages"][1]["content"]
    assert "MULTIPLICACAO" in conteudo      # o próprio nó
    assert "multiplicativa" in conteudo     # a regra do nó
    assert "ADICAO" in conteudo             # o nó pai
    assert "LITERAL_INTEIRO" in conteudo    # os filhos diretos
    assert "programa" in conteudo           # a gramática acompanha o contexto


def test_contexto_erro_sintatico_tem_regra_e_diagnostico(monkeypatch):
    registro = {}
    monkeypatch.setattr(ia, "_post_json", fake_ok(registro))
    status, _ = ia.gerar_explicacao("ERRO_SINTATICO", "int x = 5", 0, None)
    assert status == 200
    conteudo = registro["dados"]["messages"][1]["content"]
    assert "era esperado ';'" in conteudo
    assert "declaracao = tipo declarador" in conteudo


def test_pergunta_padrao_quando_nao_ha_pergunta(monkeypatch):
    registro = {}
    monkeypatch.setattr(ia, "_post_json", fake_ok(registro))
    ia.gerar_explicacao("TOKEN", "int x;", 0, None)
    conteudo = registro["dados"]["messages"][1]["content"]
    assert "Pergunta:" in conteudo


# ----------------------------------------------------------------------
# Erros de entrada (400)
# ----------------------------------------------------------------------

def test_tipo_desconhecido_vira_400(monkeypatch):
    monkeypatch.setattr(ia, "_post_json", fake_ok())
    status, corpo = ia.gerar_explicacao("OUTRO", "int x;", 0, None)
    assert status == 400
    assert "erro" in corpo


def test_alvo_inexistente_vira_400(monkeypatch):
    monkeypatch.setattr(ia, "_post_json", fake_ok())
    status, corpo = ia.gerar_explicacao("NO_AST", CODIGO_REF, 999, None)
    assert status == 400
    assert "erro" in corpo


def test_pergunta_longa_vira_400(monkeypatch):
    monkeypatch.setattr(ia, "_post_json", fake_ok())
    status, corpo = ia.gerar_explicacao("PERGUNTA", "int x;", None, "a" * 501)
    assert status == 400


def test_pergunta_vazia_vira_400(monkeypatch):
    monkeypatch.setattr(ia, "_post_json", fake_ok())
    status, _ = ia.gerar_explicacao("PERGUNTA", "int x;", None, "   ")
    assert status == 400


# ----------------------------------------------------------------------
# Falhas do Ollama (503, 504, 502)
# ----------------------------------------------------------------------

def test_conexao_recusada_vira_503_apos_uma_retentativa(monkeypatch):
    registro = {}
    monkeypatch.setattr(ia, "_post_json", fake_falha_chat(ConnectionRefusedError(), registro))
    status, corpo = ia.gerar_explicacao("PERGUNTA", "int x;", None, "Oi?")
    assert status == 503
    assert registro["chat"] == 2   # uma tentativa e uma nova tentativa
    assert "indisponível" in corpo["erro"]


def test_timeout_vira_504_sem_retentativa(monkeypatch):
    registro = {}
    monkeypatch.setattr(ia, "_post_json", fake_falha_chat(TimeoutError(), registro))
    status, corpo = ia.gerar_explicacao("PERGUNTA", "int x;", None, "Oi?")
    assert status == 504
    assert registro["chat"] == 1   # sem nova tentativa em timeout


def test_resposta_vazia_vira_502(monkeypatch):
    monkeypatch.setattr(ia, "_post_json", fake_chat(lambda: {"message": {"content": "   "}}))
    status, corpo = ia.gerar_explicacao("PERGUNTA", "int x;", None, "Oi?")
    assert status == 502


def test_json_invalido_vira_502(monkeypatch):
    def estourar():
        raise ValueError("JSON inválido")
    monkeypatch.setattr(ia, "_post_json", fake_chat(estourar))
    status, corpo = ia.gerar_explicacao("PERGUNTA", "int x;", None, "Oi?")
    assert status == 502


def test_modelo_ausente_vira_503(monkeypatch):
    def _post(url, dados, timeout):
        if url.endswith("/api/tags"):
            return {"models": [{"name": "outromodelo"}]}
        return {"message": {"content": "não deveria chegar aqui"}}
    monkeypatch.setattr(ia, "_post_json", _post)
    status, corpo = ia.gerar_explicacao("PERGUNTA", "int x;", None, "Oi?")
    assert status == 503


def test_mensagens_de_erro_nao_expoem_endereco(monkeypatch):
    registro = {}
    casos = [
        fake_falha_chat(ConnectionRefusedError(), registro),
        fake_falha_chat(TimeoutError(), registro),
        fake_chat(lambda: {"message": {"content": ""}}),
    ]
    for fake in casos:
        monkeypatch.setattr(ia, "_post_json", fake)
        _, corpo = ia.gerar_explicacao("PERGUNTA", "int x;", None, "Oi?")
        assert "ollama" not in corpo["erro"].lower()
        assert "11434" not in corpo["erro"]
    for texto in (ia.MSG_INDISPONIVEL, ia.MSG_TIMEOUT, ia.MSG_RESPOSTA_INVALIDA):
        assert "11434" not in texto and "ollama" not in texto.lower()


# ----------------------------------------------------------------------
# Endpoint HTTP e regressão
# ----------------------------------------------------------------------

def test_endpoint_ia_explicar(cliente, monkeypatch):
    monkeypatch.setattr(ia, "_post_json", fake_ok())
    resposta = cliente.post("/api/ia/explicar", json={
        "tipo": "NO_AST", "codigo": CODIGO_REF, "alvo": 4,
        "pergunta": "Por que a multiplicação está abaixo da adição?"
    })
    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["geradoPorIA"] is True
    assert corpo["explicacao"]


def test_endpoint_ia_corpo_invalido(cliente):
    resposta = cliente.post("/api/ia/explicar", data="x", content_type="text/plain")
    assert resposta.status_code == 400


def test_analisar_funciona_com_ia_indisponivel(cliente, monkeypatch):
    # A análise não depende do Ollama: derrubar o _post_json não afeta /api/analisar.
    def cair(*_args, **_kwargs):
        raise ConnectionRefusedError()
    monkeypatch.setattr(ia, "_post_json", cair)
    resposta = cliente.post("/api/analisar", json={"codigo": CODIGO_REF})
    assert resposta.status_code == 200
    assert resposta.get_json()["sintatico"]["sucesso"] is True


# ----------------------------------------------------------------------
# Integração real (pulada por padrão)
# ----------------------------------------------------------------------

@pytest.mark.skipif(os.environ.get("OLLAMA_INTEGRACAO") != "1", reason="integração real do Ollama desativada")
def test_integracao_real_ollama():
    status, corpo = ia.gerar_explicacao("PERGUNTA", CODIGO_REF, None,
                                        "Explique em uma frase o que é um parser.")
    assert status == 200
    assert corpo["explicacao"].strip() != ""
