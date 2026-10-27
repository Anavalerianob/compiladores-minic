const { test } = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");

const {
  EXEMPLOS, MENSAGENS, validarCodigo, iniciar, nomeCategoria, formatarTransicao,
  contarPorCategoria, indicePorPosicao, montarSegmentos
} = require("../app.js");

const HTML = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");

function montarTela(fetchFalso, temporizador) {
  const dom = new JSDOM(HTML);
  const doc = dom.window.document;
  const chamadas = [];
  const fetchFn = async function (url, opcoes) {
    chamadas.push({ url: url, opcoes: opcoes });
    return fetchFalso(url, opcoes);
  };
  iniciar(doc, fetchFn, temporizador);
  return {
    doc: doc,
    chamadas: chamadas,
    campo: doc.getElementById("codigo"),
    seletor: doc.getElementById("exemplos"),
    botao: doc.getElementById("analisar"),
    resultado: doc.getElementById("resultado"),
    secao: doc.getElementById("analise-lexica"),
    info: doc.getElementById("passo-info"),
    linhasTabela: function () { return doc.querySelectorAll("#corpo-tokens tr"); },
    evento: function (nome) { return new dom.window.Event(nome, { bubbles: true }); },
    tecla: function (alvo, tecla) {
      alvo.dispatchEvent(new dom.window.KeyboardEvent("keydown", { key: tecla, bubbles: true }));
    }
  };
}

function respostaJson(status, corpo) {
  return { ok: status >= 200 && status < 300, status: status, json: async () => corpo };
}

function token(tipo, lexema, linha, coluna, transicoes) {
  return { tipo: tipo, lexema: lexema, linha: linha, coluna: coluna, transicoes: transicoes || [] };
}

// Resposta do contrato da etapa 3 para o código "int numero = 10;".
const TOKENS_DECLARACAO = [
  token("PALAVRA_RESERVADA", "int", 1, 1),
  token("IDENTIFICADOR", "numero", 1, 5),
  token("OPERADOR", "=", 1, 12),
  token("LITERAL_INTEIRO", "10", 1, 14, [
    { de: "inicial", caractere: "1", para: "inteiro" },
    { de: "inteiro", caractere: "0", para: "inteiro" }
  ]),
  token("DELIMITADOR", ";", 1, 16)
];

const respostaSucesso = () =>
  respostaJson(200, {
    recebido: true,
    sucesso: true,
    mensagem: "Análise léxica concluída sem erros: 5 token(s) reconhecido(s).",
    linhas: 1,
    caracteres: 16,
    tokens: TOKENS_DECLARACAO,
    erros: []
  });

// Resposta do contrato da etapa 3 para o código "int a = 5 @ 2;".
const MENSAGEM_ERRO_ARROBA = "Erro léxico na linha 1, coluna 11: caractere não reconhecido '@'. " +
  "Verifique se ele faz parte do subconjunto suportado.";

const respostaComErro = () =>
  respostaJson(200, {
    recebido: true,
    sucesso: false,
    mensagem: "Análise léxica concluída com 1 erro(s) léxico(s) e 6 token(s) reconhecido(s).",
    linhas: 1,
    caracteres: 14,
    tokens: [
      token("PALAVRA_RESERVADA", "int", 1, 1), token("IDENTIFICADOR", "a", 1, 5), token("OPERADOR", "=", 1, 7),
      token("LITERAL_INTEIRO", "5", 1, 9), token("LITERAL_INTEIRO", "2", 1, 13), token("DELIMITADOR", ";", 1, 14)
    ],
    erros: [{ tipo: "ERRO_LEXICO", lexema: "@", linha: 1, coluna: 11, mensagem: MENSAGEM_ERRO_ARROBA }]
  });

async function analisarDeclaracao(temporizador) {
  const tela = montarTela(respostaSucesso, temporizador);
  tela.campo.value = "int numero = 10;";
  await clicarEAguardar(tela);
  return tela;
}

function temporizadorFalso() {
  return {
    funcao: null,
    intervalo: null,
    limpezas: 0,
    definir: function (funcao, intervalo) { this.funcao = funcao; this.intervalo = intervalo; return 1; },
    limpar: function () { this.funcao = null; this.limpezas += 1; }
  };
}

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
  assert.match(tela.resultado.textContent, /Análise léxica concluída sem erros/);
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

// Testes das funções auxiliares da análise léxica

test("nomeCategoria e formatarTransicao produzem textos legíveis", () => {
  assert.strictEqual(nomeCategoria("LITERAL_REAL"), "Literal real");
  assert.strictEqual(nomeCategoria("DESCONHECIDO"), "DESCONHECIDO");
  assert.strictEqual(formatarTransicao({ de: "inicial", caractere: "1", para: "inteiro" }), "inicial --'1'--> inteiro");
});

test("contarPorCategoria inclui todas as categorias", () => {
  const contagem = contarPorCategoria(TOKENS_DECLARACAO);
  assert.deepStrictEqual(contagem, {
    PALAVRA_RESERVADA: 1, IDENTIFICADOR: 1, LITERAL_INTEIRO: 1, LITERAL_REAL: 0, OPERADOR: 1, DELIMITADOR: 1
  });
});

test("indicePorPosicao converte linha e coluna em índice no texto", () => {
  assert.strictEqual(indicePorPosicao("ab\ncd", 1, 1), 0);
  assert.strictEqual(indicePorPosicao("ab\ncd", 2, 2), 4);
  assert.strictEqual(indicePorPosicao("ab\ncd", 5, 1), -1);
  // Caractere fora do plano básico ocupa duas posições em UTF-16, mas uma coluna.
  assert.strictEqual(indicePorPosicao("😀a", 1, 2), 2);
});

test("montarSegmentos separa texto simples, tokens e erros", () => {
  const segmentos = montarSegmentos("a @ // x", [token("IDENTIFICADOR", "a", 1, 1)],
    [{ tipo: "ERRO_LEXICO", lexema: "@", linha: 1, coluna: 3, mensagem: "" }]);
  assert.deepStrictEqual(segmentos.map((s) => [s.tipo, s.texto]), [
    ["token", "a"], ["texto", " "], ["erro", "@"], ["texto", " // x"]
  ]);
});

// Testes da exibição da análise léxica

test("a seção da análise léxica fica oculta no início", () => {
  const tela = montarTela(respostaSucesso);
  assert.strictEqual(tela.secao.hidden, true);
  assert.match(tela.doc.body.textContent, /Fase disponível: análise léxica \(scanner\)/);
  assert.ok(tela.doc.querySelector("details summary"));
});

test("a tabela de tokens é preenchida com categoria, lexema, linha e coluna", async () => {
  const tela = await analisarDeclaracao();
  assert.strictEqual(tela.secao.hidden, false);
  const linhas = tela.linhasTabela();
  assert.strictEqual(linhas.length, 5);
  const celulas = Array.from(linhas[1].querySelectorAll("td")).map((td) => td.textContent);
  assert.deepStrictEqual(celulas, ["2", "Identificador", "numero", "1", "5"]);
  assert.strictEqual(tela.resultado.className, "resultado sucesso");
});

test("o código destacado tem um span por token com a classe da categoria", async () => {
  const tela = await analisarDeclaracao();
  const destacado = tela.doc.getElementById("codigo-destacado");
  assert.strictEqual(destacado.textContent, "int numero = 10;");
  const spans = destacado.querySelectorAll("span.tk");
  assert.strictEqual(spans.length, 5);
  assert.strictEqual(spans[1].className.includes("tk-IDENTIFICADOR"), true);
  assert.strictEqual(spans[1].textContent, "numero");
  assert.strictEqual(spans[1].dataset.indice, "1");
  assert.strictEqual(spans[3].className.includes("tk-LITERAL_INTEIRO"), true);
});

test("a contagem mostra os totais por categoria e de erros", async () => {
  const tela = await analisarDeclaracao();
  const texto = tela.doc.getElementById("contagem").textContent;
  assert.match(texto, /Identificador: 1/);
  assert.match(texto, /Literal real: 0/);
  assert.match(texto, /Total de tokens: 5\. Erros léxicos: 0/);
  assert.strictEqual(tela.doc.getElementById("lista-erros").textContent, MENSAGENS.semErros);
});

test("erros léxicos são listados, destacados e usam o estilo de erro", async () => {
  const tela = montarTela(respostaComErro);
  tela.campo.value = "int a = 5 @ 2;";
  await clicarEAguardar(tela);
  assert.strictEqual(tela.resultado.className, "resultado erro");
  assert.match(tela.resultado.textContent, /1 erro\(s\) léxico\(s\)/);
  const itens = tela.doc.querySelectorAll("#lista-erros li");
  assert.strictEqual(itens.length, 1);
  assert.strictEqual(itens[0].textContent, MENSAGEM_ERRO_ARROBA);
  const erro = tela.doc.querySelector("#codigo-destacado .tk-erro");
  assert.strictEqual(erro.textContent, "@");
  assert.match(tela.doc.getElementById("contagem").textContent, /Erros léxicos: 1/);
});

test("resposta fora do contrato exibe erro inesperado e mantém a seção oculta", async () => {
  const tela = montarTela(() => respostaJson(200, { recebido: true, mensagem: "ok", linhas: 1, caracteres: 6 }));
  tela.campo.value = "int a;";
  await clicarEAguardar(tela);
  assert.strictEqual(tela.resultado.textContent, MENSAGENS.inesperado);
  assert.strictEqual(tela.resultado.className, "resultado erro");
  assert.strictEqual(tela.secao.hidden, true);
});

// Testes do passo a passo

test("o passo a passo começa no primeiro token e permite avançar e voltar", async () => {
  const tela = await analisarDeclaracao();
  const anterior = tela.doc.getElementById("passo-anterior");
  const proximo = tela.doc.getElementById("passo-proximo");
  assert.match(tela.info.textContent, /Token 1 de 5: lexema 'int' na linha 1, coluna 1/);
  assert.strictEqual(anterior.getAttribute("aria-disabled"), "true");

  proximo.click();
  assert.match(tela.info.textContent, /Token 2 de 5: lexema 'numero' na linha 1, coluna 5/);
  assert.match(tela.info.textContent, /Categoria: Identificador\./);
  assert.strictEqual(tela.doc.querySelector('#codigo-destacado [data-indice="1"]').classList.contains("atual"), true);
  assert.strictEqual(tela.linhasTabela()[1].classList.contains("atual"), true);
  assert.strictEqual(tela.doc.querySelectorAll("#codigo-destacado .atual").length, 1);

  anterior.click();
  assert.match(tela.info.textContent, /Token 1 de 5/);
  anterior.click();
  assert.match(tela.info.textContent, /Token 1 de 5/);
});

test("o passo a passo exibe as transições do autômato", async () => {
  const tela = await analisarDeclaracao();
  tela.linhasTabela()[3].click();
  const transicoes = Array.from(tela.info.querySelectorAll("li")).map((li) => li.textContent);
  assert.deepStrictEqual(transicoes, ["inicial --'1'--> inteiro", "inteiro --'0'--> inteiro"]);
});

test("as setas do teclado avançam e voltam no passo a passo", async () => {
  const tela = await analisarDeclaracao();
  const proximo = tela.doc.getElementById("passo-proximo");
  tela.tecla(proximo, "ArrowRight");
  tela.tecla(proximo, "ArrowRight");
  assert.match(tela.info.textContent, /Token 3 de 5/);
  tela.tecla(proximo, "ArrowLeft");
  assert.match(tela.info.textContent, /Token 2 de 5/);
});

test("a reprodução automática avança até o último token e para", async () => {
  const relogio = temporizadorFalso();
  const tela = await analisarDeclaracao(relogio);
  const reproduzir = tela.doc.getElementById("passo-reproduzir");
  reproduzir.click();
  assert.strictEqual(reproduzir.textContent, "Pausar");
  assert.strictEqual(reproduzir.getAttribute("aria-pressed"), "true");
  assert.strictEqual(relogio.intervalo, 900);
  for (let i = 0; i < 4; i++) relogio.funcao();
  assert.match(tela.info.textContent, /Token 5 de 5: lexema ';'/);
  assert.strictEqual(reproduzir.textContent, "Reproduzir");
  assert.strictEqual(reproduzir.getAttribute("aria-pressed"), "false");
  assert.strictEqual(relogio.funcao, null);
});

test("a reprodução pode ser pausada e usa a velocidade escolhida", async () => {
  const relogio = temporizadorFalso();
  const tela = await analisarDeclaracao(relogio);
  const reproduzir = tela.doc.getElementById("passo-reproduzir");
  const velocidade = tela.doc.getElementById("passo-velocidade");
  velocidade.value = "rapida";
  velocidade.dispatchEvent(tela.evento("change"));
  reproduzir.click();
  assert.strictEqual(relogio.intervalo, 400);
  velocidade.value = "lenta";
  velocidade.dispatchEvent(tela.evento("change"));
  assert.strictEqual(relogio.intervalo, 1600);
  relogio.funcao();
  reproduzir.click();
  assert.strictEqual(reproduzir.textContent, "Reproduzir");
  assert.strictEqual(relogio.funcao, null);
  assert.match(tela.info.textContent, /Token 2 de 5/);
});

test("clicar em uma linha da tabela seleciona o token no passo a passo", async () => {
  const tela = await analisarDeclaracao();
  tela.linhasTabela()[4].click();
  assert.match(tela.info.textContent, /Token 5 de 5: lexema ';'/);
  assert.strictEqual(tela.linhasTabela()[4].getAttribute("aria-current"), "true");
  assert.strictEqual(tela.linhasTabela()[0].classList.contains("atual"), false);
});

// Testes dos estados da interface depois de uma análise

test("editar o código depois da análise exibe aviso", async () => {
  const tela = await analisarDeclaracao();
  tela.campo.value = "int numero = 20;";
  tela.campo.dispatchEvent(tela.evento("input"));
  assert.strictEqual(tela.resultado.textContent, MENSAGENS.alterado);
  assert.strictEqual(tela.resultado.className, "resultado info");
});

test("trocar de exemplo oculta a análise anterior", async () => {
  const tela = await analisarDeclaracao();
  tela.seletor.value = "erro";
  tela.seletor.dispatchEvent(tela.evento("change"));
  assert.strictEqual(tela.secao.hidden, true);
});

test("entrada vazia depois de uma análise oculta a seção", async () => {
  const tela = await analisarDeclaracao();
  tela.campo.value = "";
  await clicarEAguardar(tela);
  assert.strictEqual(tela.resultado.textContent, MENSAGENS.vazio);
  assert.strictEqual(tela.secao.hidden, true);
});

test("falha de rede depois de uma análise oculta a seção", async () => {
  let falhar = false;
  const tela = montarTela(() => {
    if (falhar) throw new TypeError("Failed to fetch");
    return respostaSucesso();
  });
  tela.campo.value = "int numero = 10;";
  await clicarEAguardar(tela);
  assert.strictEqual(tela.secao.hidden, false);
  falhar = true;
  await clicarEAguardar(tela);
  assert.strictEqual(tela.resultado.textContent, MENSAGENS.comunicacao);
  assert.strictEqual(tela.secao.hidden, true);
});

test("exemplo de erros léxicos contém os três tipos de erro previstos", () => {
  assert.match(EXEMPLOS.erro.codigo, /7\.5\.1/);
  assert.match(EXEMPLOS.erro.codigo, /@/);
  assert.match(EXEMPLOS.erro.codigo, /\/\*/);
  assert.doesNotMatch(EXEMPLOS.erro.codigo, /\*\//);
});

// Teste de segurança

test("lexemas e mensagens com marcação HTML são exibidos como texto", async () => {
  const codigo = "<b>x</b>";
  const tela = montarTela(() => respostaJson(200, {
    recebido: true,
    sucesso: false,
    mensagem: "Análise léxica concluída com 1 erro(s) léxico(s) e 1 token(s) reconhecido(s).",
    linhas: 1,
    caracteres: codigo.length,
    tokens: [token("IDENTIFICADOR", "<b>x</b>", 1, 1)],
    erros: [{ tipo: "ERRO_LEXICO", lexema: "<", linha: 1, coluna: 1, mensagem: "<img src=x onerror=alert(1)>" }]
  }));
  tela.campo.value = codigo;
  await clicarEAguardar(tela);
  assert.strictEqual(tela.doc.querySelector("#analise-lexica b"), null);
  assert.strictEqual(tela.doc.querySelector("#analise-lexica img"), null);
  assert.strictEqual(tela.linhasTabela()[0].querySelector("code").textContent, "<b>x</b>");
  assert.match(tela.info.textContent, /lexema '<b>x<\/b>'/);
  assert.strictEqual(tela.doc.querySelector("#lista-erros li").textContent, "<img src=x onerror=alert(1)>");
});
