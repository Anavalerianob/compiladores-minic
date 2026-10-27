const EXEMPLOS = {
  declaracao: {
    titulo: "Exemplo 1: Declaração e inicialização de variáveis",
    codigo: "int numero = 10;\nfloat media = 7.5;\nint contador;"
  },
  aritmetica: {
    titulo: "Exemplo 2: Operações aritméticas",
    codigo: "int a = 10;\nint b = 5;\nint resultado = (a + b) * 2 - a / b;"
  },
  condicional: {
    titulo: "Exemplo 3: Estrutura condicional",
    codigo: "int numero = 10;\nif (numero > 0) {\n    numero = numero + 1;\n} else {\n    numero = 0;\n}"
  },
  comentarios: {
    titulo: "Exemplo 4: Comentários e operadores relacionais",
    codigo: "// Comentário de linha: ignorado pelo scanner\nint a = 3;\nint b = 7;\n/* Comentário de bloco\n   com mais de uma linha */\nif (a != b) {\n    a = a + 1;\n}\nif (a <= b) {\n    b = 0;\n}"
  },
  erro: {
    titulo: "Exemplo 5: Código com erros léxicos",
    codigo: "int total = 10;\nfloat media = 7.5.1;\nint x = total @ 2;\n/* comentário sem fechamento\nint y = 0;"
  }
};

const MENSAGENS = {
  vazio: "Informe um código-fonte antes de solicitar a análise.",
  espacos: "O código informado contém apenas espaços em branco. Escreva um programa antes de solicitar a análise.",
  comunicacao: "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.",
  inesperado: "Ocorreu um erro inesperado. Tente novamente mais tarde.",
  alterado: "O código foi alterado depois da última análise. Clique em Analisar para atualizar os tokens.",
  semErros: "Nenhum erro léxico encontrado.",
  semTokens: "Nenhum token reconhecido."
};

const CATEGORIAS = {
  PALAVRA_RESERVADA: {
    nome: "Palavra reservada",
    explicacao: "Palavra com significado fixo na linguagem (int, float, if, else), que não pode ser usada como nome de variável."
  },
  IDENTIFICADOR: {
    nome: "Identificador",
    explicacao: "Nome criado pelo programador; começa com letra ou '_' e continua com letras, dígitos ou '_'."
  },
  LITERAL_INTEIRO: {
    nome: "Literal inteiro",
    explicacao: "Valor numérico escrito diretamente no código, formado apenas por dígitos."
  },
  LITERAL_REAL: {
    nome: "Literal real",
    explicacao: "Valor numérico com parte decimal: dígitos, um ponto e mais dígitos."
  },
  OPERADOR: {
    nome: "Operador",
    explicacao: "Símbolo de operação aritmética, de atribuição ou de comparação. Pela regra do maior lexema, '<=' forma um único token."
  },
  DELIMITADOR: {
    nome: "Delimitador",
    explicacao: "Símbolo que separa ou agrupa partes do programa, como parênteses, chaves, ';' e ','."
  }
};

const VELOCIDADES = { lenta: 1600, normal: 900, rapida: 400 };

function validarCodigo(codigo) {
  if (codigo === "") return MENSAGENS.vazio;
  if (codigo.trim() === "") return MENSAGENS.espacos;
  return null;
}

function nomeCategoria(tipo) {
  return CATEGORIAS[tipo] ? CATEGORIAS[tipo].nome : tipo;
}

function formatarTransicao(transicao) {
  return transicao.de + " --'" + transicao.caractere + "'--> " + transicao.para;
}

function contarPorCategoria(tokens) {
  const contagem = {};
  for (const tipo of Object.keys(CATEGORIAS)) contagem[tipo] = 0;
  for (const token of tokens) contagem[token.tipo] = (contagem[token.tipo] || 0) + 1;
  return contagem;
}

// O backend conta colunas por caractere (ponto de código), e as strings do
// JavaScript usam UTF-16; por isso o índice é calculado percorrendo o texto.
function criarConversorPosicao(codigo) {
  const linhas = [[]];
  let indice = 0;
  for (const caractere of codigo) {
    linhas[linhas.length - 1].push(indice);
    indice += caractere.length;
    if (caractere === "\n") linhas.push([]);
  }
  linhas[linhas.length - 1].push(indice);
  return function (linha, coluna) {
    const colunas = linhas[linha - 1];
    if (!colunas || coluna < 1 || coluna > colunas.length) return -1;
    return colunas[coluna - 1];
  };
}

function indicePorPosicao(codigo, linha, coluna) {
  return criarConversorPosicao(codigo)(linha, coluna);
}

// Divide o código em trechos de texto simples, tokens e erros, na ordem em que aparecem.
function montarSegmentos(codigo, tokens, erros) {
  const posicao = criarConversorPosicao(codigo);
  const marcas = [];
  tokens.forEach(function (token, indice) {
    marcas.push({ tipo: "token", categoria: token.tipo, indice: indice, lexema: token.lexema, inicio: posicao(token.linha, token.coluna) });
  });
  erros.forEach(function (erro, indice) {
    marcas.push({ tipo: "erro", indice: indice, lexema: erro.lexema, inicio: posicao(erro.linha, erro.coluna) });
  });
  marcas.sort(function (a, b) { return a.inicio - b.inicio; });

  const segmentos = [];
  let cursor = 0;
  for (const marca of marcas) {
    const fim = marca.inicio + marca.lexema.length;
    if (marca.inicio < cursor || codigo.slice(marca.inicio, fim) !== marca.lexema) continue;
    if (marca.inicio > cursor) segmentos.push({ tipo: "texto", texto: codigo.slice(cursor, marca.inicio) });
    segmentos.push({ tipo: marca.tipo, categoria: marca.categoria, indice: marca.indice, texto: marca.lexema });
    cursor = fim;
  }
  if (cursor < codigo.length) segmentos.push({ tipo: "texto", texto: codigo.slice(cursor) });
  return segmentos;
}

async function enviarCodigo(codigo, fetchFn) {
  let resposta;
  try {
    resposta = await fetchFn("/api/analisar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codigo: codigo })
    });
  } catch (_erro) {
    return { tipo: "erro", texto: MENSAGENS.comunicacao };
  }

  let dados;
  try {
    dados = await resposta.json();
  } catch (_erro) {
    if ([502, 503, 504].includes(resposta.status)) {
      return { tipo: "erro", texto: MENSAGENS.comunicacao };
    }
    return { tipo: "erro", texto: MENSAGENS.inesperado };
  }

  if (resposta.ok && dados && dados.recebido) {
    if (!Array.isArray(dados.tokens) || !Array.isArray(dados.erros)) {
      return { tipo: "erro", texto: MENSAGENS.inesperado };
    }
    return {
      tipo: dados.sucesso ? "sucesso" : "erro",
      texto: dados.mensagem + " Linhas: " + dados.linhas + ". Caracteres: " + dados.caracteres + ".",
      analise: { codigo: codigo, tokens: dados.tokens, erros: dados.erros }
    };
  }
  if (resposta.status === 400 && dados && dados.erro) {
    return { tipo: "erro", texto: dados.erro };
  }
  return { tipo: "erro", texto: MENSAGENS.inesperado };
}

function iniciar(doc, fetchFn, temporizador) {
  const relogio = temporizador || {
    definir: function (funcao, intervalo) { return setInterval(funcao, intervalo); },
    limpar: function (id) { clearInterval(id); }
  };

  const campo = doc.getElementById("codigo");
  const seletor = doc.getElementById("exemplos");
  const botao = doc.getElementById("analisar");
  const resultado = doc.getElementById("resultado");
  const secao = doc.getElementById("analise-lexica");
  const contagem = doc.getElementById("contagem");
  const destacado = doc.getElementById("codigo-destacado");
  const corpoTokens = doc.getElementById("corpo-tokens");
  const listaErros = doc.getElementById("lista-erros");
  const info = doc.getElementById("passo-info");
  const anterior = doc.getElementById("passo-anterior");
  const proximo = doc.getElementById("passo-proximo");
  const reproduzir = doc.getElementById("passo-reproduzir");
  const velocidade = doc.getElementById("passo-velocidade");

  let analise = null;
  let atual = -1;
  let reproducao = null;

  function mostrar(tipo, texto) {
    resultado.textContent = texto;
    resultado.className = "resultado " + tipo;
  }

  function elemento(tag, texto, classe) {
    const el = doc.createElement(tag);
    if (texto !== undefined) el.textContent = texto;
    if (classe) el.className = classe;
    return el;
  }

  function totalTokens() {
    return analise ? analise.tokens.length : 0;
  }

  // Passo a passo

  function pausar() {
    if (reproducao !== null) {
      relogio.limpar(reproducao);
      reproducao = null;
    }
    reproduzir.textContent = "Reproduzir";
    reproduzir.setAttribute("aria-pressed", "false");
  }

  function atualizarControles() {
    const n = totalTokens();
    anterior.setAttribute("aria-disabled", String(atual <= 0));
    proximo.setAttribute("aria-disabled", String(atual >= n - 1));
    reproduzir.setAttribute("aria-disabled", String(n === 0));
  }

  function atualizarInfo() {
    const n = totalTokens();
    if (n === 0) {
      info.replaceChildren(elemento("p", MENSAGENS.semTokens));
      return;
    }
    const token = analise.tokens[atual];
    const categoria = CATEGORIAS[token.tipo];
    const transicoes = elemento("ol");
    for (const transicao of token.transicoes || []) {
      transicoes.appendChild(elemento("li", formatarTransicao(transicao)));
    }
    info.replaceChildren(
      elemento("p", "Token " + (atual + 1) + " de " + n + ": lexema '" + token.lexema + "' na linha " + token.linha + ", coluna " + token.coluna),
      elemento("p", "Categoria: " + nomeCategoria(token.tipo) + ". " + (categoria ? categoria.explicacao : "")),
      elemento("p", "Transições do autômato:"),
      transicoes
    );
  }

  function selecionar(indice) {
    if (indice < 0 || indice >= totalTokens()) return;
    atual = indice;
    for (const el of secao.querySelectorAll(".atual")) {
      el.classList.remove("atual");
      el.removeAttribute("aria-current");
    }
    const seletorIndice = '[data-indice="' + indice + '"]';
    const span = destacado.querySelector(seletorIndice);
    const linha = corpoTokens.querySelector(seletorIndice);
    if (span) span.classList.add("atual");
    if (linha) {
      linha.classList.add("atual");
      linha.setAttribute("aria-current", "true");
    }
    atualizarControles();
    atualizarInfo();
  }

  function passoAutomatico() {
    if (atual < totalTokens() - 1) selecionar(atual + 1);
    if (atual >= totalTokens() - 1) pausar();
  }

  function iniciarReproducao() {
    reproducao = relogio.definir(passoAutomatico, VELOCIDADES[velocidade.value] || VELOCIDADES.normal);
  }

  function alternarReproducao() {
    if (reproducao !== null) {
      pausar();
      return;
    }
    if (totalTokens() === 0) return;
    if (atual >= totalTokens() - 1) selecionar(0);
    iniciarReproducao();
    reproduzir.textContent = "Pausar";
    reproduzir.setAttribute("aria-pressed", "true");
  }

  function voltar() {
    pausar();
    selecionar(atual - 1);
  }

  function avancar() {
    pausar();
    selecionar(atual + 1);
  }

  // Exibição da análise

  function renderizarContagem() {
    const porCategoria = contarPorCategoria(analise.tokens);
    const lista = elemento("ul", undefined, "lista-contagem");
    for (const tipo of Object.keys(CATEGORIAS)) {
      const item = elemento("li");
      item.append(elemento("span", nomeCategoria(tipo), "tk tk-" + tipo), doc.createTextNode(": " + porCategoria[tipo]));
      lista.appendChild(item);
    }
    contagem.replaceChildren(
      lista,
      elemento("p", "Total de tokens: " + analise.tokens.length + ". Erros léxicos: " + analise.erros.length)
    );
  }

  function renderizarCodigo() {
    const fragmento = doc.createDocumentFragment();
    for (const segmento of montarSegmentos(analise.codigo, analise.tokens, analise.erros)) {
      if (segmento.tipo === "texto") {
        fragmento.appendChild(doc.createTextNode(segmento.texto));
      } else if (segmento.tipo === "token") {
        const span = elemento("span", segmento.texto, "tk tk-" + segmento.categoria);
        span.dataset.indice = String(segmento.indice);
        span.title = nomeCategoria(segmento.categoria);
        fragmento.appendChild(span);
      } else {
        const span = elemento("span", segmento.texto, "tk-erro");
        span.title = "Erro léxico";
        fragmento.appendChild(span);
      }
    }
    destacado.replaceChildren(fragmento);
  }

  function renderizarTabela() {
    const fragmento = doc.createDocumentFragment();
    analise.tokens.forEach(function (token, indice) {
      const linha = elemento("tr");
      linha.dataset.indice = String(indice);
      linha.tabIndex = 0;
      const celulaLexema = elemento("td");
      celulaLexema.appendChild(elemento("code", token.lexema));
      linha.append(
        elemento("td", String(indice + 1)),
        elemento("td", nomeCategoria(token.tipo)),
        celulaLexema,
        elemento("td", String(token.linha)),
        elemento("td", String(token.coluna))
      );
      linha.addEventListener("click", function () {
        pausar();
        selecionar(indice);
      });
      linha.addEventListener("keydown", function (evento) {
        if (evento.key === "Enter" || evento.key === " ") {
          evento.preventDefault();
          pausar();
          selecionar(indice);
        }
      });
      fragmento.appendChild(linha);
    });
    corpoTokens.replaceChildren(fragmento);
  }

  function renderizarErros() {
    if (analise.erros.length === 0) {
      listaErros.replaceChildren(elemento("li", MENSAGENS.semErros));
      return;
    }
    listaErros.replaceChildren.apply(listaErros, analise.erros.map(function (erro) {
      return elemento("li", erro.mensagem);
    }));
  }

  function exibirAnalise(dados) {
    pausar();
    analise = dados;
    atual = 0;
    renderizarContagem();
    renderizarCodigo();
    renderizarTabela();
    renderizarErros();
    secao.hidden = false;
    if (totalTokens() > 0) {
      selecionar(0);
    } else {
      atualizarControles();
      atualizarInfo();
    }
  }

  function ocultarAnalise() {
    pausar();
    analise = null;
    atual = -1;
    secao.hidden = true;
  }

  // Eventos

  anterior.addEventListener("click", voltar);
  proximo.addEventListener("click", avancar);
  reproduzir.addEventListener("click", alternarReproducao);

  velocidade.addEventListener("change", function () {
    if (reproducao !== null) {
      relogio.limpar(reproducao);
      iniciarReproducao();
    }
  });

  secao.addEventListener("keydown", function (evento) {
    if (evento.target.tagName === "SELECT" || !analise) return;
    if (evento.key === "ArrowRight") {
      evento.preventDefault();
      avancar();
    } else if (evento.key === "ArrowLeft") {
      evento.preventDefault();
      voltar();
    }
  });

  campo.addEventListener("input", function () {
    if (analise) mostrar("info", MENSAGENS.alterado);
  });

  seletor.addEventListener("change", function () {
    const exemplo = EXEMPLOS[seletor.value];
    if (exemplo) {
      ocultarAnalise();
      campo.value = exemplo.codigo;
      mostrar("info", "Exemplo carregado. Você pode editá-lo antes de analisar.");
    }
  });

  botao.addEventListener("click", async function () {
    const codigo = campo.value;
    const erro = validarCodigo(codigo);
    if (erro) {
      ocultarAnalise();
      mostrar("erro", erro);
      return;
    }

    botao.disabled = true;
    pausar();
    mostrar("info", "Enviando código ao servidor...");
    try {
      const retorno = await enviarCodigo(codigo, fetchFn);
      mostrar(retorno.tipo, retorno.texto);
      if (retorno.analise) {
        exibirAnalise(retorno.analise);
      } else {
        ocultarAnalise();
      }
    } finally {
      botao.disabled = false;
    }
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    EXEMPLOS, MENSAGENS, CATEGORIAS, VELOCIDADES, validarCodigo, nomeCategoria, formatarTransicao,
    contarPorCategoria, indicePorPosicao, montarSegmentos, enviarCodigo, iniciar
  };
} else {
  document.addEventListener("DOMContentLoaded", function () {
    iniciar(document, window.fetch.bind(window));
  });
}
