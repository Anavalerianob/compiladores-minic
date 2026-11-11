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
  },
  precedencia: {
    titulo: "Exemplo 6: Precedência e associatividade (AST)",
    codigo: "int resultado = 10 + 5 * 2;\nint r = 20 - 5 - 3;\nint m = (10 + 5) * 2;"
  },
  aninhado: {
    titulo: "Exemplo 7: if, else if e else com blocos aninhados",
    codigo: "if (a > 0) {\n    int x = 1;\n    if (x < 10) {\n        x = x + 1;\n    } else {\n        x = 0;\n    }\n} else if (a < 0) {\n    int y = 2;\n} else {\n    int z = 3;\n}"
  },
  erro_sintatico: {
    titulo: "Exemplo 8: Código com erros sintáticos",
    codigo: "int a = 10;\nif (a > 0 {\n    a = 1;\n}\nb = ;"
  }
};

// Categoria exibida junto do rotulo de cada no da AST (marca em texto).
const CATEGORIAS_NO = {
  PROGRAMA: { marca: "Programa", classe: "marca-Programa" },
  DECLARACAO_VARIAVEL: { marca: "Declaração", classe: "marca-Declaracao" },
  ATRIBUICAO: { marca: "Comando", classe: "marca-Comando" },
  CONDICIONAL: { marca: "Comando", classe: "marca-Comando" },
  BLOCO: { marca: "Comando", classe: "marca-Comando" },
  ADICAO: { marca: "Operação", classe: "marca-Operacao" },
  SUBTRACAO: { marca: "Operação", classe: "marca-Operacao" },
  MULTIPLICACAO: { marca: "Operação", classe: "marca-Operacao" },
  DIVISAO: { marca: "Operação", classe: "marca-Operacao" },
  COMPARACAO: { marca: "Operação", classe: "marca-Operacao" },
  NEGACAO: { marca: "Operação", classe: "marca-Operacao" },
  IDENTIFICADOR: { marca: "Valor", classe: "marca-Valor" },
  LITERAL_INTEIRO: { marca: "Valor", classe: "marca-Valor" },
  LITERAL_REAL: { marca: "Valor", classe: "marca-Valor" }
};

function categoriaNo(tipo) {
  return CATEGORIAS_NO[tipo] || { marca: tipo, classe: "marca-Programa" };
}

// Lista, em ordem, os nos cuja ordem de criacao e menor ou igual a passo. Como os
// filhos sao criados antes do pai (pos-ordem), um no com ordem <= passo tem toda a
// subarvore ja criada; devolvemos as raizes dessas subarvores.
function raizesDoPasso(no, passo) {
  if (no.ordem <= passo) return [no];
  let raizes = [];
  for (const filho of no.filhos) raizes = raizes.concat(raizesDoPasso(filho, passo));
  return raizes;
}

function aplanarAst(no, saida) {
  saida = saida || [];
  saida.push(no);
  for (const filho of no.filhos) aplanarAst(filho, saida);
  return saida;
}

function tiposDaAst(no) {
  const vistos = [];
  for (const atual of aplanarAst(no)) {
    if (vistos.indexOf(atual.tipo) === -1) vistos.push(atual.tipo);
  }
  return vistos;
}

function exportarAst(ast) {
  return JSON.stringify(ast, null, 2);
}

const MENSAGENS = {
  vazio: "Informe um código-fonte antes de solicitar a análise.",
  espacos: "O código informado contém apenas espaços em branco. Escreva um programa antes de solicitar a análise.",
  comunicacao: "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.",
  inesperado: "Ocorreu um erro inesperado. Tente novamente mais tarde.",
  alterado: "O código foi alterado depois da última análise. Clique em Analisar para atualizar os tokens.",
  semErros: "Nenhum erro léxico encontrado.",
  semTokens: "Nenhum token reconhecido.",
  astVazia: "O programa não tem comandos nem declarações: a AST tem apenas o nó Programa.",
  semArvore: "Sem árvore para mostrar.",
  iaCarregando: "Gerando explicação...",
  iaSemCodigo: "Analise um código antes de pedir uma explicação."
};

// Sugestoes do professor virtual (perguntas prontas sobre a analise sintatica).
const SUGESTOES_IA = [
  "Qual a diferença entre o scanner e o parser?",
  "O que são terminais e não terminais em uma gramática?",
  "Qual a diferença entre a AST e a árvore de derivação?",
  "Como funciona a precedência de operadores no MiniC?",
  "O que é um parser descendente recursivo?",
  "O que é recursão à esquerda e por que evitá-la?"
];

const ROTULOS_PAPEL = {
  item: "item do programa ou bloco",
  tipo: "tipo",
  valor: "valor (expressão atribuída)",
  esquerda: "operando à esquerda",
  direita: "operando à direita",
  operando: "operando",
  condicao: "condição",
  entao: "bloco executado quando a condição é verdadeira (então)",
  senao: "bloco ou condicional do else (senão)"
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
    const sintatico = dados.sintatico || null;
    const erroSintatico = sintatico && sintatico.executado && !sintatico.sucesso;
    return {
      tipo: dados.sucesso && !erroSintatico ? "sucesso" : "erro",
      texto: dados.mensagem + " Linhas: " + dados.linhas + ". Caracteres: " + dados.caracteres + ".",
      analise: { codigo: codigo, tokens: dados.tokens, erros: dados.erros, sintatico: sintatico }
    };
  }
  if (resposta.status === 400 && dados && dados.erro) {
    return { tipo: "erro", texto: dados.erro };
  }
  return { tipo: "erro", texto: MENSAGENS.inesperado };
}

async function enviarPergunta(corpo, fetchFn) {
  let resposta;
  try {
    resposta = await fetchFn("/api/ia/explicar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo)
    });
  } catch (_erro) {
    return { tipo: "erro", texto: MENSAGENS.comunicacao };
  }

  let dados;
  try {
    dados = await resposta.json();
  } catch (_erro) {
    return { tipo: "erro", texto: MENSAGENS.inesperado };
  }

  if (resposta.ok && dados && typeof dados.explicacao === "string" && dados.explicacao !== "") {
    return { tipo: "sucesso", explicacao: dados.explicacao };
  }
  if (dados && dados.erro) {
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

  // Elementos da analise sintatica (etapa 4).
  const secaoSintatica = doc.getElementById("analise-sintatica");
  const situacao = doc.getElementById("sintatico-situacao");
  const secaoErrosSint = doc.getElementById("secao-erros-sintaticos");
  const listaErrosSint = doc.getElementById("lista-erros-sintaticos");
  const secaoArvore = doc.getElementById("secao-arvore");
  const arvore = doc.getElementById("arvore-ast");
  const noDetalhes = doc.getElementById("no-detalhes");
  const astFiltro = doc.getElementById("ast-filtro");
  const astExpandir = doc.getElementById("ast-expandir");
  const astRecolher = doc.getElementById("ast-recolher");
  const astExportar = doc.getElementById("ast-exportar");
  const astAnteriorBtn = doc.getElementById("ast-anterior");
  const astProximoBtn = doc.getElementById("ast-proximo");
  const astReproduzirBtn = doc.getElementById("ast-reproduzir");
  const astVelocidade = doc.getElementById("ast-velocidade");
  const astCompletaBtn = doc.getElementById("ast-arvore-completa");
  const astPassoInfo = doc.getElementById("ast-passo-info");
  const iaResposta = doc.getElementById("ia-resposta");
  const iaPergunta = doc.getElementById("ia-pergunta");
  const iaEnviar = doc.getElementById("ia-enviar");
  const iaSugestoes = doc.getElementById("ia-sugestoes");

  let analise = null;
  let iaOcupado = false;
  let atual = -1;
  let reproducao = null;

  // Estado da arvore da AST.
  let astRaiz = null;
  let nosPorId = {};
  let nosPorOrdem = {};
  let totalNos = 0;
  let noSelecionado = null;
  let astPasso = null;       // null = arvore completa; k = passo da construcao
  let astReproducao = null;

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
      transicoes,
      botaoIa("Explicar com IA", { tipo: "TOKEN", alvo: atual })
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
    listaErros.replaceChildren.apply(listaErros, analise.erros.map(function (erro, indice) {
      const item = doc.createElement("li");
      item.appendChild(elemento("p", erro.mensagem, "erro-campo"));
      item.appendChild(botaoIa("Entender erro com IA", { tipo: "ERRO_LEXICO", alvo: indice }));
      return item;
    }));
  }

  function exibirAnalise(dados) {
    pausar();
    analise = dados;
    atual = 0;
    secao.classList.remove("desatualizada");
    secaoSintatica.classList.remove("desatualizada");
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
    exibirSintatico(dados.sintatico);
  }

  function ocultarAnalise() {
    pausar();
    astPausar();
    analise = null;
    atual = -1;
    astRaiz = null;
    secao.hidden = true;
    secaoSintatica.hidden = true;
  }

  // ----- Analise sintatica e AST -----

  function limparDestaqueAst() {
    for (const el of destacado.querySelectorAll(".no-destaque")) el.classList.remove("no-destaque");
    for (const el of corpoTokens.querySelectorAll(".no-destaque")) el.classList.remove("no-destaque");
  }

  function exibirSintatico(sintatico) {
    astPausar();
    iaResposta.replaceChildren();
    iaResposta.className = "";
    situacao.textContent = "";
    listaErrosSint.replaceChildren();
    secaoErrosSint.hidden = true;
    secaoArvore.hidden = true;
    noDetalhes.replaceChildren();
    astRaiz = null;
    noSelecionado = null;
    limparDestaqueAst();

    if (!sintatico) {
      secaoSintatica.hidden = true;
      return;
    }
    secaoSintatica.hidden = false;

    if (!sintatico.executado) {
      situacao.textContent = sintatico.motivo ||
        "A análise sintática não foi executada porque há erros léxicos. Corrija-os e analise novamente.";
      return;
    }

    if (!sintatico.sucesso) {
      situacao.textContent = "O código tem erros sintáticos. A AST não foi construída.";
      renderizarErrosSintaticos(sintatico.erros || []);
      return;
    }

    astRaiz = sintatico.ast;
    situacao.textContent = "";
    prepararArvore();
  }

  function renderizarErrosSintaticos(lista) {
    secaoErrosSint.hidden = false;
    const fragmento = doc.createDocumentFragment();
    lista.forEach(function (erro, indice) {
      const item = doc.createElement("li");
      item.appendChild(elemento("span", "Erro sintático", "erro-rotulo"));
      item.appendChild(elemento("p", erro.mensagem, "erro-campo"));
      if (Array.isArray(erro.esperado) && erro.esperado.length > 0) {
        item.appendChild(campoErro("Esperado: ", traduzirEsperado(erro.esperado)));
      }
      if (erro.encontrado) item.appendChild(campoErro("Encontrado: ", erro.encontrado));
      if (erro.regra) item.appendChild(campoErro("Regra violada: ", erro.regra));
      item.appendChild(botaoIa("Entender erro com IA", { tipo: "ERRO_SINTATICO", alvo: indice }));
      fragmento.appendChild(item);
    });
    listaErrosSint.replaceChildren(fragmento);
  }

  function campoErro(chave, valor) {
    const p = elemento("p", undefined, "erro-campo");
    p.append(elemento("span", chave, "chave"), doc.createTextNode(valor));
    return p;
  }

  function traduzirEsperado(esperado) {
    const nomes = { IDENTIFICADOR: "um identificador", LITERAL_INTEIRO: "um número inteiro", LITERAL_REAL: "um número real" };
    return esperado.map(function (item) { return nomes[item] || "'" + item + "'"; }).join(", ");
  }

  // Monta o indice de nos e prepara a arvore completa.
  function prepararArvore() {
    nosPorId = {};
    nosPorOrdem = {};
    const planos = aplanarAst(astRaiz);
    totalNos = planos.length;
    for (const no of planos) {
      nosPorId[no.id] = no;
      nosPorOrdem[no.ordem] = no;
    }
    prepararFiltro();
    secaoArvore.hidden = false;
    astPasso = null;
    montarArvore([astRaiz], null);
    astPassoInfo.replaceChildren(elemento("p",
      "Árvore completa: " + totalNos + " nó(s). Use Próximo ou as setas para ver a construção passo a passo."));
    atualizarControlesAst();
  }

  function prepararFiltro() {
    const opcoes = [elemento("option", "Todos os nós")];
    opcoes[0].value = "";
    for (const tipo of tiposDaAst(astRaiz)) {
      const op = elemento("option", tipo);
      op.value = tipo;
      opcoes.push(op);
    }
    astFiltro.replaceChildren.apply(astFiltro, opcoes);
  }

  function criarNoElemento(no, nivel, ordemDestaque) {
    const li = doc.createElement("li");
    li.setAttribute("role", "treeitem");
    li.setAttribute("aria-level", String(nivel));
    li.dataset.id = String(no.id);
    li.dataset.tipo = no.tipo;
    li.dataset.ordem = String(no.ordem);
    li.tabIndex = -1;
    if (ordemDestaque !== null && no.ordem === ordemDestaque) li.classList.add("no-criado");

    const linha = elemento("div", undefined, "no-linha");
    const temFilhos = no.filhos.length > 0;
    const alternar = elemento("span", temFilhos ? "▾" : "", "no-alternar");
    const cat = categoriaNo(no.tipo);
    linha.append(
      alternar,
      elemento("span", no.rotulo, "no-rotulo"),
      elemento("span", cat.marca, "no-marca " + cat.classe)
    );
    li.appendChild(linha);

    if (temFilhos) {
      li.setAttribute("aria-expanded", "true");
      const grupo = doc.createElement("ul");
      grupo.setAttribute("role", "group");
      for (const filho of no.filhos) grupo.appendChild(criarNoElemento(filho, nivel + 1, ordemDestaque));
      li.appendChild(grupo);
      alternar.addEventListener("click", function (evento) {
        evento.stopPropagation();
        alternarExpansao(li);
      });
    }

    linha.addEventListener("click", function () { selecionarNo(no.id); });
    return li;
  }

  function montarArvore(raizes, ordemDestaque) {
    const fragmento = doc.createDocumentFragment();
    for (const raiz of raizes) fragmento.appendChild(criarNoElemento(raiz, 1, ordemDestaque));
    arvore.replaceChildren(fragmento);
    const primeiro = arvore.querySelector('[role="treeitem"]');
    if (primeiro) primeiro.tabIndex = 0;
  }

  function alternarExpansao(li, forcar) {
    if (li.getAttribute("aria-expanded") === null) return;
    const expandir = forcar === undefined ? li.getAttribute("aria-expanded") === "false" : forcar;
    li.setAttribute("aria-expanded", expandir ? "true" : "false");
    const alternar = li.querySelector(":scope > .no-linha > .no-alternar");
    if (alternar) alternar.textContent = expandir ? "▾" : "▸";
  }

  function selecionarNo(id) {
    const no = nosPorId[id];
    if (!no) return;
    noSelecionado = id;
    for (const el of arvore.querySelectorAll('[aria-selected="true"]')) el.removeAttribute("aria-selected");
    for (const el of arvore.querySelectorAll('[role="treeitem"]')) el.tabIndex = -1;
    const li = arvore.querySelector('[data-id="' + id + '"]');
    if (li) {
      li.setAttribute("aria-selected", "true");
      li.tabIndex = 0;
      if (typeof li.focus === "function") li.focus();
    }
    destacarCodigoETokens(no);
    mostrarDetalhes(no);
  }

  function destacarCodigoETokens(no) {
    limparDestaqueAst();
    if (no.tokenInicio === null || no.tokenInicio === undefined) return;
    for (let i = no.tokenInicio; i <= no.tokenFim; i++) {
      const span = destacado.querySelector('[data-indice="' + i + '"]');
      if (span) span.classList.add("no-destaque");
      const linha = corpoTokens.querySelector('tr[data-indice="' + i + '"]');
      if (linha) linha.classList.add("no-destaque");
    }
  }

  function mostrarDetalhes(no) {
    const dl = doc.createElement("dl");
    function par(chave, valor) {
      dl.append(elemento("dt", chave), elemento("dd", valor));
    }
    par("Tipo", no.tipo);
    par("Rótulo", no.rotulo);
    par("Regra da gramática", no.regra);
    par("Papel", no.papel ? (ROTULOS_PAPEL[no.papel] || no.papel) : "raiz da árvore");
    par("Posição", "linha " + no.linha + ", coluna " + no.coluna + " até linha " + no.linhaFim + ", coluna " + no.colunaFim);
    par("Tokens", no.tokenInicio === null ? "nenhum" : (no.tokenInicio + " a " + no.tokenFim));
    const atributos = Object.keys(no.atributos || {});
    if (atributos.length > 0) {
      par("Atributos", atributos.map(function (k) { return k + ": " + no.atributos[k]; }).join(", "));
    }
    noDetalhes.replaceChildren(
      elemento("h3", "Nó selecionado"), dl,
      botaoIa("Explicar com IA", { tipo: "NO_AST", alvo: no.id })
    );
  }

  // Navegacao por teclado na arvore.
  function nosVisiveis() {
    return Array.from(arvore.querySelectorAll('[role="treeitem"]')).filter(function (li) {
      let pai = li.parentElement;
      while (pai && pai !== arvore) {
        if (pai.getAttribute("role") === "group") {
          const ancestral = pai.parentElement;
          if (ancestral && ancestral.getAttribute("aria-expanded") === "false") return false;
        }
        pai = pai.parentElement;
      }
      return true;
    });
  }

  function navegarArvore(evento) {
    const alvo = evento.target.closest ? evento.target.closest('[role="treeitem"]') : null;
    if (!alvo || !arvore.contains(alvo)) return;
    const visiveis = nosVisiveis();
    const indice = visiveis.indexOf(alvo);
    if (evento.key === "ArrowDown") {
      evento.preventDefault();
      if (indice < visiveis.length - 1) focarNo(visiveis[indice + 1]);
    } else if (evento.key === "ArrowUp") {
      evento.preventDefault();
      if (indice > 0) focarNo(visiveis[indice - 1]);
    } else if (evento.key === "ArrowRight") {
      evento.preventDefault();
      if (alvo.getAttribute("aria-expanded") === "false") alternarExpansao(alvo, true);
    } else if (evento.key === "ArrowLeft") {
      evento.preventDefault();
      if (alvo.getAttribute("aria-expanded") === "true") alternarExpansao(alvo, false);
    } else if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      selecionarNo(Number(alvo.dataset.id));
    }
  }

  function focarNo(li) {
    for (const el of arvore.querySelectorAll('[role="treeitem"]')) el.tabIndex = -1;
    li.tabIndex = 0;
    if (typeof li.focus === "function") li.focus();
  }

  function expandirTudo(expandir) {
    for (const li of arvore.querySelectorAll('[role="treeitem"][aria-expanded]')) alternarExpansao(li, expandir);
  }

  function filtrar(valor) {
    if (!valor) {
      for (const li of arvore.querySelectorAll('[role="treeitem"]')) li.classList.remove("esmaecido");
      return;
    }
    expandirTudo(true);
    for (const li of arvore.querySelectorAll('[role="treeitem"]')) {
      li.classList.toggle("esmaecido", li.dataset.tipo !== valor);
    }
  }

  function baixarAst() {
    if (!astRaiz) return;
    const texto = exportarAst(astRaiz);
    try {
      const blob = new (doc.defaultView.Blob)([texto], { type: "application/json" });
      const url = doc.defaultView.URL.createObjectURL(blob);
      const link = doc.createElement("a");
      link.href = url;
      link.download = "ast-minic.json";
      doc.body.appendChild(link);
      link.click();
      doc.body.removeChild(link);
      doc.defaultView.URL.revokeObjectURL(url);
    } catch (_erro) {
      // Ambiente sem suporte a Blob/URL (ex.: alguns testes): a exportacao e opcional.
    }
  }

  // Passo a passo da construcao.
  function astPausar() {
    if (astReproducao !== null) {
      relogio.limpar(astReproducao);
      astReproducao = null;
    }
    astReproduzirBtn.textContent = "Reproduzir";
    astReproduzirBtn.setAttribute("aria-pressed", "false");
  }

  function atualizarControlesAst() {
    astAnteriorBtn.setAttribute("aria-disabled", String(astPasso === null || astPasso <= 1));
    astProximoBtn.setAttribute("aria-disabled", String(astPasso !== null && astPasso >= totalNos));
    astReproduzirBtn.setAttribute("aria-disabled", String(totalNos === 0));
  }

  function irParaPasso(k) {
    astPasso = k;
    const criado = nosPorOrdem[k];
    montarArvore(raizesDoPasso(astRaiz, k), k);
    destacarCodigoETokens(criado);
    const lexemas = lexemasDoNo(criado);
    astPassoInfo.replaceChildren(elemento("p",
      "Passo " + k + " de " + totalNos + ": o parser reconheceu " + criado.rotulo +
      " pela regra " + criado.regra + ", a partir dos tokens " + lexemas + "."));
    atualizarControlesAst();
  }

  function lexemasDoNo(no) {
    if (no.tokenInicio === null || no.tokenInicio === undefined) return "(nenhum)";
    const partes = [];
    for (let i = no.tokenInicio; i <= no.tokenFim && i < analise.tokens.length; i++) {
      partes.push(analise.tokens[i].lexema);
    }
    return partes.join(" ");
  }

  function astProximo() {
    astPausar();
    if (astPasso === null) irParaPasso(1);
    else if (astPasso < totalNos) irParaPasso(astPasso + 1);
  }

  function astAnterior() {
    astPausar();
    if (astPasso !== null && astPasso > 1) irParaPasso(astPasso - 1);
  }

  function astArvoreCompleta() {
    astPausar();
    astPasso = null;
    montarArvore([astRaiz], null);
    limparDestaqueAst();
    astPassoInfo.replaceChildren(elemento("p",
      "Árvore completa: " + totalNos + " nó(s). Use Próximo ou as setas para ver a construção passo a passo."));
    atualizarControlesAst();
  }

  function astPassoAutomatico() {
    if (astPasso !== null && astPasso < totalNos) irParaPasso(astPasso + 1);
    if (astPasso !== null && astPasso >= totalNos) astPausar();
  }

  function astAlternarReproducao() {
    if (astReproducao !== null) { astPausar(); return; }
    if (totalNos === 0) return;
    if (astPasso === null || astPasso >= totalNos) irParaPasso(1);
    astReproducao = relogio.definir(astPassoAutomatico, VELOCIDADES[astVelocidade.value] || VELOCIDADES.normal);
    astReproduzirBtn.textContent = "Pausar";
    astReproduzirBtn.setAttribute("aria-pressed", "true");
  }

  // ----- Explicações com IA -----
  // A interface nunca fala com o Ollama: só chama /api/ia/explicar.

  function botaoIa(texto, opcoes) {
    const botao = elemento("button", texto, "botao-ia");
    botao.type = "button";
    botao.addEventListener("click", function () {
      pedirExplicacao(Object.assign({ botao: botao }, opcoes));
    });
    return botao;
  }

  async function pedirExplicacao(opcoes) {
    if (iaOcupado) return;
    const codigo = (analise && analise.codigo) || campo.value;
    if (!codigo || codigo.trim() === "") {
      mostrarIaResposta({ tipo: "erro", texto: MENSAGENS.iaSemCodigo });
      return;
    }
    iaOcupado = true;
    const botao = opcoes.botao || null;
    if (botao) botao.disabled = true;
    iaEnviar.disabled = true;
    iaResposta.className = "";
    iaResposta.replaceChildren(elemento("p", MENSAGENS.iaCarregando));
    try {
      const corpo = { tipo: opcoes.tipo, codigo: codigo };
      if (opcoes.alvo !== undefined && opcoes.alvo !== null) corpo.alvo = opcoes.alvo;
      if (opcoes.pergunta) corpo.pergunta = opcoes.pergunta;
      const retorno = await enviarPergunta(corpo, fetchFn);
      mostrarIaResposta(retorno);
    } finally {
      iaOcupado = false;
      if (botao) botao.disabled = false;
      iaEnviar.disabled = false;
    }
  }

  function mostrarIaResposta(retorno) {
    if (retorno.tipo === "sucesso") {
      iaResposta.className = "";
      const paragrafos = retorno.explicacao.split(/\n\s*\n|\n/).filter(function (t) { return t.trim() !== ""; });
      const frag = doc.createDocumentFragment();
      for (const texto of paragrafos) frag.appendChild(elemento("p", texto));
      iaResposta.replaceChildren(frag);
    } else {
      iaResposta.className = "ia-erro";
      iaResposta.replaceChildren(elemento("p", retorno.texto));
    }
  }

  function montarSugestoesIa() {
    const frag = doc.createDocumentFragment();
    for (const pergunta of SUGESTOES_IA) {
      const botao = elemento("button", pergunta);
      botao.type = "button";
      botao.addEventListener("click", function () {
        iaPergunta.value = pergunta;
        pedirExplicacao({ tipo: "PERGUNTA", pergunta: pergunta, botao: botao });
      });
      frag.appendChild(botao);
    }
    iaSugestoes.replaceChildren(frag);
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

  astAnteriorBtn.addEventListener("click", astAnterior);
  astProximoBtn.addEventListener("click", astProximo);
  astReproduzirBtn.addEventListener("click", astAlternarReproducao);
  astCompletaBtn.addEventListener("click", astArvoreCompleta);
  astExpandir.addEventListener("click", function () { expandirTudo(true); });
  astRecolher.addEventListener("click", function () { expandirTudo(false); });
  astExportar.addEventListener("click", baixarAst);
  astFiltro.addEventListener("change", function () { filtrar(astFiltro.value); });
  arvore.addEventListener("keydown", navegarArvore);

  astVelocidade.addEventListener("change", function () {
    if (astReproducao !== null) {
      relogio.limpar(astReproducao);
      astReproducao = relogio.definir(astPassoAutomatico, VELOCIDADES[astVelocidade.value] || VELOCIDADES.normal);
    }
  });

  iaEnviar.addEventListener("click", function () {
    pedirExplicacao({ tipo: "PERGUNTA", pergunta: iaPergunta.value, botao: iaEnviar });
  });
  montarSugestoesIa();

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
    if (analise) {
      mostrar("info", MENSAGENS.alterado);
      secao.classList.add("desatualizada");
      if (!secaoSintatica.hidden) secaoSintatica.classList.add("desatualizada");
    }
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
    EXEMPLOS, MENSAGENS, CATEGORIAS, CATEGORIAS_NO, SUGESTOES_IA, VELOCIDADES, validarCodigo,
    nomeCategoria, formatarTransicao, contarPorCategoria, indicePorPosicao, montarSegmentos,
    categoriaNo, raizesDoPasso, aplanarAst, tiposDaAst, exportarAst, enviarCodigo, enviarPergunta, iniciar
  };
} else {
  document.addEventListener("DOMContentLoaded", function () {
    iniciar(document, window.fetch.bind(window));
  });
}
