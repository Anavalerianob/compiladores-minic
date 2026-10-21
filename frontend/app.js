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
  erro: {
    titulo: "Exemplo 4: Código com erro intencional",
    codigo: "int x = ;\nfloat y = 3.5"
  }
};

const MENSAGENS = {
  vazio: "Informe um código-fonte antes de solicitar a análise.",
  espacos: "O código informado contém apenas espaços em branco. Escreva um programa antes de solicitar a análise.",
  comunicacao: "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.",
  inesperado: "Ocorreu um erro inesperado. Tente novamente mais tarde."
};

function validarCodigo(codigo) {
  if (codigo === "") return MENSAGENS.vazio;
  if (codigo.trim() === "") return MENSAGENS.espacos;
  return null;
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

  if (resposta.ok && dados.recebido) {
    return {
      tipo: "sucesso",
      texto: dados.mensagem + " Linhas: " + dados.linhas + ". Caracteres: " + dados.caracteres + "."
    };
  }
  if (resposta.status === 400 && dados.erro) {
    return { tipo: "erro", texto: dados.erro };
  }
  return { tipo: "erro", texto: MENSAGENS.inesperado };
}

function iniciar(doc, fetchFn) {
  const campo = doc.getElementById("codigo");
  const seletor = doc.getElementById("exemplos");
  const botao = doc.getElementById("analisar");
  const resultado = doc.getElementById("resultado");

  function mostrar(tipo, texto) {
    resultado.textContent = texto;
    resultado.className = "resultado " + tipo;
  }

  seletor.addEventListener("change", function () {
    const exemplo = EXEMPLOS[seletor.value];
    if (exemplo) {
      campo.value = exemplo.codigo;
      mostrar("info", "Exemplo carregado. Você pode editá-lo antes de analisar.");
    }
  });

  botao.addEventListener("click", async function () {
    const codigo = campo.value;
    const erro = validarCodigo(codigo);
    if (erro) {
      mostrar("erro", erro);
      return;
    }

    botao.disabled = true;
    mostrar("info", "Enviando código ao servidor...");
    try {
      const retorno = await enviarCodigo(codigo, fetchFn);
      mostrar(retorno.tipo, retorno.texto);
    } finally {
      botao.disabled = false;
    }
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { EXEMPLOS, MENSAGENS, validarCodigo, enviarCodigo, iniciar };
} else {
  document.addEventListener("DOMContentLoaded", function () {
    iniciar(document, window.fetch.bind(window));
  });
}
