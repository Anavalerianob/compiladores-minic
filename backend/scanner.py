"""Analisador lexico (scanner) do subconjunto MiniC.

O codigo-fonte e percorrido caractere a caractere, simulando um automato finito
deterministico escrito a mao. Cada token guarda as transicoes de estado percorridas
para reconhecer o seu lexema, o que permite exibir o reconhecimento passo a passo.
Os erros lexicos sao acumulados e a analise continua a partir do caractere seguinte.
"""

import string

PALAVRAS_RESERVADAS = ("int", "float", "if", "else")

LETRAS = string.ascii_letters + "_"
DIGITOS = "0123456789"
ESPACOS = " \t\r\n"
OPERADORES_SIMPLES = "+-*"
DELIMITADORES = "(){};,"
CONTINUACAO_NUMERO = LETRAS + DIGITOS + "."

# Estado alcancado pelo primeiro caractere dos operadores que podem ser seguidos de "=".
ESTADOS_RELACIONAIS = {"=": "igual", "<": "menor", ">": "maior", "!": "exclamacao"}

# Sentinela devolvida ao olhar alem do fim do texto; nao pertence a nenhum conjunto acima.
FIM = "\0"


def analisar(codigo):
    """Retorna {"tokens": [...], "erros": [...]} para o codigo-fonte informado."""
    return _Scanner(codigo).executar()


class _Scanner:
    def __init__(self, codigo):
        self.codigo = codigo
        self.pos = 0
        self.linha = 1
        self.coluna = 1
        self.tokens = []
        self.erros = []

    def executar(self):
        while self.pos < len(self.codigo):
            c = self._atual()
            if c in ESPACOS:
                self._avancar()
            elif c in LETRAS:
                self._identificador()
            elif c in DIGITOS:
                self._numero()
            elif c == "/":
                self._barra()
            elif c in ESTADOS_RELACIONAIS:
                self._relacional()
            elif c in OPERADORES_SIMPLES:
                self._simples("operador", "OPERADOR")
            elif c in DELIMITADORES:
                self._simples("delimitador", "DELIMITADOR")
            else:
                self._erro(
                    c, self.linha, self.coluna,
                    f"caractere não reconhecido '{c}'. Verifique se ele faz parte do subconjunto suportado.",
                )
                self._avancar()
        return {"tokens": self.tokens, "erros": self.erros}

    # Leitura do texto

    def _atual(self, deslocamento=0):
        indice = self.pos + deslocamento
        return self.codigo[indice] if indice < len(self.codigo) else FIM

    def _avancar(self):
        c = self.codigo[self.pos]
        self.pos += 1
        if c == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c

    def _transitar(self, transicoes, de, para):
        """Consome o caractere atual, registra a transicao e retorna o novo estado."""
        transicoes.append({"de": de, "caractere": self._avancar(), "para": para})
        return para

    # Registro de resultados

    def _token(self, tipo, inicio, linha, coluna, transicoes):
        self.tokens.append({
            "tipo": tipo,
            "lexema": self.codigo[inicio:self.pos],
            "linha": linha,
            "coluna": coluna,
            "transicoes": transicoes,
        })

    def _erro(self, lexema, linha, coluna, descricao):
        self.erros.append({
            "tipo": "ERRO_LEXICO",
            "lexema": lexema,
            "linha": linha,
            "coluna": coluna,
            "mensagem": f"Erro léxico na linha {linha}, coluna {coluna}: {descricao}",
        })

    # Reconhecimento de cada categoria

    def _identificador(self):
        inicio, linha, coluna = self.pos, self.linha, self.coluna
        transicoes = []
        estado = "inicial"
        while self._atual() in LETRAS or self._atual() in DIGITOS:
            estado = self._transitar(transicoes, estado, "identificador")
        lexema = self.codigo[inicio:self.pos]
        tipo = "PALAVRA_RESERVADA" if lexema in PALAVRAS_RESERVADAS else "IDENTIFICADOR"
        self._token(tipo, inicio, linha, coluna, transicoes)

    def _numero(self):
        inicio, linha, coluna = self.pos, self.linha, self.coluna
        transicoes = []
        estado = "inicial"
        while self._atual() in DIGITOS:
            estado = self._transitar(transicoes, estado, "inteiro")
        if self._atual() == ".":
            estado = self._transitar(transicoes, estado, "ponto_decimal")
            while self._atual() in DIGITOS:
                estado = self._transitar(transicoes, estado, "real")

        # Pela regra do maior lexema, o trecho colado ao numero faz parte do mesmo erro.
        if estado == "ponto_decimal" or self._atual() in CONTINUACAO_NUMERO:
            while self._atual() in CONTINUACAO_NUMERO:
                self._avancar()
            trecho = self.codigo[inicio:self.pos]
            self._erro(trecho, linha, coluna, f"literal numérico malformado '{trecho}'. {_dica_numero(trecho)}")
            return

        tipo = "LITERAL_REAL" if estado == "real" else "LITERAL_INTEIRO"
        self._token(tipo, inicio, linha, coluna, transicoes)

    def _barra(self):
        inicio, linha, coluna = self.pos, self.linha, self.coluna
        proximo = self._atual(1)

        if proximo == "/":
            while self.pos < len(self.codigo) and self._atual() != "\n":
                self._avancar()
            return

        if proximo == "*":
            self._avancar()
            self._avancar()
            while self.pos < len(self.codigo):
                if self._atual() == "*" and self._atual(1) == "/":
                    self._avancar()
                    self._avancar()
                    return
                self._avancar()
            self._erro("/*", linha, coluna, "comentário de bloco iniciado com '/*' não foi fechado com '*/'.")
            return

        transicoes = []
        self._transitar(transicoes, "inicial", "barra")
        self._token("OPERADOR", inicio, linha, coluna, transicoes)

    def _relacional(self):
        inicio, linha, coluna = self.pos, self.linha, self.coluna
        primeiro = self._atual()
        transicoes = []
        estado = self._transitar(transicoes, "inicial", ESTADOS_RELACIONAIS[primeiro])
        if self._atual() == "=":
            self._transitar(transicoes, estado, "operador")
        elif primeiro == "!":
            self._erro(
                "!", linha, coluna,
                "caractere '!' isolado não é reconhecido. O operador suportado é '!=' (diferente).",
            )
            return
        self._token("OPERADOR", inicio, linha, coluna, transicoes)

    def _simples(self, estado, tipo):
        inicio, linha, coluna = self.pos, self.linha, self.coluna
        transicoes = []
        self._transitar(transicoes, "inicial", estado)
        self._token(tipo, inicio, linha, coluna, transicoes)


def _dica_numero(trecho):
    if any(c in LETRAS for c in trecho):
        return "Um número não pode ter letras coladas; um identificador deve começar com letra ou '_'."
    if trecho.count(".") > 1:
        return "Um literal real deve ter apenas um ponto decimal (por exemplo, 3.5)."
    return "Um literal real deve ter dígitos depois do ponto (por exemplo, 3.0)."
