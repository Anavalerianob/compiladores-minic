const { test } = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");

const { EXEMPLOS, MENSAGENS, validarCodigo, iniciar } = require("../app.js");

const HTML = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");

function montarTela(fetchFalso) {
  const dom = new JSDOM(HTML);
  const doc = dom.window.document;
  const chamadas = [];
  const fetchFn = async function (url, opcoes) {
    chamadas.push({ url: url, opcoes: opcoes });
    return fetchFalso(url, opcoes);
  };
  iniciar(doc, fetchFn);
  return {
    doc: doc,
    chamadas: chamadas,
    campo: doc.getElementById("codigo"),
    seletor: doc.getElementById("exemplos"),
    botao: doc.getElementById("analisar"),
    resultado: doc.getElementById("resultado"),
    evento: function (nome) { return new dom.window.Event(nome); }
  };
}

function respostaJson(status, corpo) {
  return { ok: status >= 200 && status < 300, status: status, json: async () => corpo };
}

const respostaSucesso = () =>
  respostaJson(200, { recebido: true, mensagem: "Código recebido com sucesso.", linhas: 1, caracteres: 16 });

async function clicarEAguardar(tela) {
  tela.botao.click();
  await new Promise((resolver) => setTimeout(resolver, 0));
}

// Testes da tela principal

test("exibe identificação do sistema e linguagem", () => {
  const tela = montarTela(respostaSucesso);
  assert.match(tela.doc.querySelector("h1").textContent, /MiniC Analisador/);
  assert.match(tela.doc.body.textContent, /linguagem C/);
});

test("exibe campo de código, botão, seletor e área de resultados", () => {
  const tela = montarTela(respostaSucesso);
  assert.ok(tela.campo);
  assert.strictEqual(tela.campo.tagName, "TEXTAREA");
  assert.strictEqual(tela.botao.textContent, "Analisar");
  assert.ok(tela.seletor);
  assert.ok(tela.resultado);
});

// Testes dos exemplos

test("existem pelo menos três exemplos", () => {
  assert.ok(Object.keys(EXEMPLOS).length >= 3);
});

for (const chave of Object.keys(EXEMPLOS)) {
  test("seleção do exemplo '" + chave + "' carrega o código correspondente", () => {
    const tela = montarTela(respostaSucesso);
    tela.seletor.value = chave;
    tela.seletor.dispatchEvent(tela.evento("change"));
    assert.strictEqual(tela.campo.value, EXEMPLOS[chave].codigo);
  });
}

test("selecionar um novo exemplo substitui o conteúdo anterior", () => {
  const tela = montarTela(respostaSucesso);
  tela.campo.value = "texto antigo";
  tela.seletor.value = "aritmetica";
  tela.seletor.dispatchEvent(tela.evento("change"));
  assert.strictEqual(tela.campo.value, EXEMPLOS.aritmetica.codigo);
  tela.seletor.value = "condicional";
  tela.seletor.dispatchEvent(tela.evento("change"));
  assert.strictEqual(tela.campo.value, EXEMPLOS.condicional.codigo);
});

test("exemplo carregado pode ser editado e o código editado é enviado", async () => {
  const tela = montarTela(respostaSucesso);
  tela.seletor.value = "declaracao";
  tela.seletor.dispatchEvent(tela.evento("change"));
  tela.campo.value = tela.campo.value + "\nint extra = 1;";
  await clicarEAguardar(tela);
  const corpo = JSON.parse(tela.chamadas[0].opcoes.body);
  assert.strictEqual(corpo.codigo, EXEMPLOS.declaracao.codigo + "\nint extra = 1;");
});

// Testes de validação no frontend

test("validarCodigo identifica vazio, espaços e código válido", () => {
  assert.strictEqual(validarCodigo(""), MENSAGENS.vazio);
  assert.strictEqual(validarCodigo("   \n\t"), MENSAGENS.espacos);
  assert.strictEqual(validarCodigo("int a;"), null);
});

test("entrada vazia exibe mensagem e não chama o servidor", async () => {
  const tela = montarTela(respostaSucesso);
  tela.campo.value = "";
  await clicarEAguardar(tela);
  assert.strictEqual(tela.resultado.textContent, MENSAGENS.vazio);
  assert.strictEqual(tela.chamadas.length, 0);
});

test("entrada só com espaços exibe mensagem e não chama o servidor", async () => {
  const tela = montarTela(respostaSucesso);
  tela.campo.value = "    \n   ";
  await clicarEAguardar(tela);
  assert.strictEqual(tela.resultado.textContent, MENSAGENS.espacos);
  assert.strictEqual(tela.chamadas.length, 0);
});

// Testes de comunicação com o backend

test("código válido é enviado via POST em JSON para /api/analisar", async () => {
  const tela = montarTela(respostaSucesso);
  tela.campo.value = "int numero = 10;";
  await clicarEAguardar(tela);
  assert.strictEqual(tela.chamadas.length, 1);
  assert.strictEqual(tela.chamadas[0].url, "/api/analisar");
  assert.strictEqual(tela.chamadas[0].opcoes.method, "POST");
  assert.deepStrictEqual(JSON.parse(tela.chamadas[0].opcoes.body), { codigo: "int numero = 10;" });
  assert.match(tela.resultado.textContent, /Código recebido com sucesso/);
  assert.strictEqual(tela.resultado.className, "resultado sucesso");
});

test("caracteres especiais são preservados no envio", async () => {
  const tela = montarTela(respostaSucesso);
  const codigo = '#include <stdio.h>\nprintf("%d\\n", 10); // ação ç';
  tela.campo.value = codigo;
  await clicarEAguardar(tela);
  assert.strictEqual(JSON.parse(tela.chamadas[0].opcoes.body).codigo, codigo);
});

test("o código permanece no campo após o envio", async () => {
  const tela = montarTela(respostaSucesso);
  tela.campo.value = "int a = 1;";
  await clicarEAguardar(tela);
  assert.strictEqual(tela.campo.value, "int a = 1;");
});

test("erro 400 do backend exibe a mensagem retornada", async () => {
  const tela = montarTela(() => respostaJson(400, { recebido: false, erro: "Requisição inválida: o campo 'codigo' é obrigatório." }));
  tela.campo.value = "int a;";
  await clicarEAguardar(tela);
  assert.match(tela.resultado.textContent, /obrigatório/);
  assert.strictEqual(tela.resultado.className, "resultado erro");
});

test("falha de rede exibe mensagem de comunicação e reabilita o botão", async () => {
  const tela = montarTela(() => { throw new TypeError("Failed to fetch"); });
  tela.campo.value = "int a;";
  await clicarEAguardar(tela);
  assert.strictEqual(tela.resultado.textContent, MENSAGENS.comunicacao);
  assert.strictEqual(tela.botao.disabled, false);
});

test("backend indisponível (502 sem JSON) exibe mensagem de comunicação", async () => {
  const tela = montarTela(() => ({ ok: false, status: 502, json: async () => { throw new SyntaxError(); } }));
  tela.campo.value = "int a;";
  await clicarEAguardar(tela);
  assert.strictEqual(tela.resultado.textContent, MENSAGENS.comunicacao);
});

test("erro 500 exibe mensagem genérica sem detalhes internos", async () => {
  const tela = montarTela(() => respostaJson(500, { erro: "Ocorreu um erro inesperado no servidor." }));
  tela.campo.value = "int a;";
  await clicarEAguardar(tela);
  assert.strictEqual(tela.resultado.textContent, MENSAGENS.inesperado);
});
