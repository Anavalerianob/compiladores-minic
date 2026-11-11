"""Analisador sintatico (parser) do subconjunto MiniC.

E um parser descendente recursivo escrito a mao: ha uma funcao por nao terminal
da gramatica (programa, declaracao, comando, expressao e as demais). Essa estrategia
foi escolhida por ser a mais didatica: cada funcao espelha uma regra da gramatica,
o que permite registrar a ordem de construcao dos nos (para o passo a passo da
interface) e citar a regra violada em cada erro sintatico.

O parser consome a lista de tokens que o scanner ja produziu; ele nao reexecuta o
scanner e nao altera os tokens. A saida publica e analisar_sintaxe(tokens).
"""

# Limite de aninhamento (parenteses, menos unario, blocos e else if somados).
# Evita que uma entrada muito aninhada estoure a recursao do Python (erro 500);
# ao passar disso, o parser gera um erro sintatico tratado.
MAX_PROFUNDIDADE = 100

# Limite de erros sintaticos registrados por analise. Acima disso o parser para
# e acrescenta um aviso de que existem mais erros.
MAX_ERROS = 20

TIPOS = ("int", "float")

OP_ADITIVO = ("+", "-")
OP_MULTIPLICATIVO = ("*", "/")
OP_RELACIONAL = ("==", "!=", "<", "<=", ">", ">=")

# Regras da gramatica, usadas no campo "regra" dos erros (texto para a interface).
REGRA_DECLARACAO = 'declaracao = tipo declarador { "," declarador } ";"'
REGRA_DECLARADOR = 'declarador = IDENTIFICADOR [ "=" expressao ]'
REGRA_ATRIBUICAO = 'atribuicao = IDENTIFICADOR "=" expressao ";"'
REGRA_CONDICIONAL = 'condicional = "if" "(" expressao ")" bloco [ "else" ( bloco | condicional ) ]'
REGRA_BLOCO = 'bloco = "{" { item } "}"'
REGRA_EXPRESSAO = 'expressao = aditiva [ op_relacional aditiva ]'
REGRA_PRIMARIA = 'primaria = IDENTIFICADOR | LITERAL_INTEIRO | LITERAL_REAL | "(" expressao ")"'
REGRA_ITEM = "item = declaracao | comando"

# Nomes de categoria de token traduzidos para texto na mensagem ao usuario.
_CATEGORIA_TEXTO = {
    "IDENTIFICADOR": "um identificador",
    "LITERAL_INTEIRO": "um numero inteiro",
    "LITERAL_REAL": "um numero real",
}

# Rotulos por tipo de no para a arvore. Nos com texto variavel montam o rotulo
# a partir dos atributos na funcao _rotulo.
_ROTULOS_FIXOS = {
    "PROGRAMA": "Programa",
    "BLOCO": "Bloco",
    "CONDICIONAL": "Condicional (if)",
    "ADICAO": "Adição (+)",
    "SUBTRACAO": "Subtração (-)",
    "MULTIPLICACAO": "Multiplicação (*)",
    "DIVISAO": "Divisão (/)",
    "NEGACAO": "Negação (-)",
}


def _rotulo(tipo, atributos):
    if tipo in _ROTULOS_FIXOS:
        return _ROTULOS_FIXOS[tipo]
    if tipo == "DECLARACAO_VARIAVEL":
        return f"Declaração: {atributos['tipoDado']} {atributos['nome']}"
    if tipo == "ATRIBUICAO":
        return f"Atribuição: {atributos['nome']}"
    if tipo == "COMPARACAO":
        return f"Comparação ({atributos['operador']})"
    if tipo == "IDENTIFICADOR":
        return f"Identificador: {atributos['nome']}"
    if tipo == "LITERAL_INTEIRO":
        return f"Literal inteiro: {atributos['valor']}"
    if tipo == "LITERAL_REAL":
        return f"Literal real: {atributos['valor']}"
    return tipo


class _ErroSintatico(Exception):
    """Carrega o dicionario do erro para ser tratado na recuperacao."""

    def __init__(self, erro):
        super().__init__(erro["mensagem"])
        self.erro = erro


def analisar_sintaxe(tokens):
    """Analisa a lista de tokens do scanner.

    Retorna {"sucesso": bool, "ast": dict ou None, "erros": [...]}. Com qualquer
    erro sintatico, sucesso e False e ast e None.
    """
    return _Parser(tokens).executar()


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.erros = []
        self.contador = 0          # ordem/id de criacao dos nos (pos-ordem)
        self.profundidade = 0      # aninhamento atual
        self.consumiu_desde_sync = True  # controle de cascata de erros
        self.limite_atingido = False

    def executar(self):
        ast = self._programa()
        sucesso = not self.erros
        return {"sucesso": sucesso, "ast": ast if sucesso else None, "erros": self.erros}

    # ------------------------------------------------------------------
    # Leitura da lista de tokens
    # ------------------------------------------------------------------

    def _atual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _fim(self):
        return self.pos >= len(self.tokens)

    def _avancar(self):
        token = self.tokens[self.pos]
        self.pos += 1
        self.consumiu_desde_sync = True
        return token

    def _lexema(self):
        token = self._atual()
        return token["lexema"] if token else None

    def _e_lexema(self, *lexemas):
        token = self._atual()
        return token is not None and token["lexema"] in lexemas

    def _e_tipo(self, *tipos):
        token = self._atual()
        return token is not None and token["tipo"] in tipos

    # ------------------------------------------------------------------
    # Construcao de nos
    # ------------------------------------------------------------------

    def _no(self, tipo, regra, atributos, filhos, token_inicio, token_fim):
        """Cria um no. filhos e uma lista de pares (papel, no_filho).

        A ordem/id e atribuida aqui (pos-ordem: todos os filhos ja foram criados
        antes de o pai chamar este metodo).
        """
        self.contador += 1
        for papel, filho in filhos:
            filho["papel"] = papel
        ti = self.tokens[token_inicio]
        tf = self.tokens[token_fim]
        return {
            "id": self.contador,
            "ordem": self.contador,
            "tipo": tipo,
            "rotulo": _rotulo(tipo, atributos),
            "regra": regra,
            "papel": None,
            "linha": ti["linha"],
            "coluna": ti["coluna"],
            "linhaFim": tf["linha"],
            "colunaFim": tf["coluna"] + len(tf["lexema"]) - 1,
            "tokenInicio": token_inicio,
            "tokenFim": token_fim,
            "atributos": atributos,
            "filhos": [filho for _, filho in filhos],
        }

    # ------------------------------------------------------------------
    # Erros e recuperacao
    # ------------------------------------------------------------------

    def _posicao_erro(self):
        """(linha, coluna) do ponto do erro: token atual ou logo apos o ultimo."""
        token = self._atual()
        if token is not None:
            return token["linha"], token["coluna"]
        if self.tokens:
            ultimo = self.tokens[-1]
            return ultimo["linha"], ultimo["coluna"] + len(ultimo["lexema"])
        return 1, 1

    def _encontrado(self):
        token = self._atual()
        return token["lexema"] if token is not None else "fim do código"

    def _erro(self, esperado, regra, clausula):
        """Monta e lanca um erro sintatico. clausula completa a mensagem padrao."""
        linha, coluna = self._posicao_erro()
        erro = {
            "tipo": "ERRO_SINTATICO",
            "linha": linha,
            "coluna": coluna,
            "encontrado": self._encontrado(),
            "esperado": esperado,
            "regra": regra,
            "mensagem": f"Erro sintático na linha {linha}, coluna {coluna}: {clausula}.",
        }
        raise _ErroSintatico(erro)

    def _registrar(self, erro):
        self.erros.append(erro)

    def _sincronizar(self):
        """Modo panico: descarta tokens ate um ponto de sincronizacao.

        Pontos: ";" (consumido), "}" (nao consumido, para fechar bloco aberto) ou
        inicio de item (int, float, if, "{" ou IDENTIFICADOR no comeco de comando).
        """
        while not self._fim():
            if self._e_lexema(";"):
                self._avancar()
                break
            if self._e_lexema("}"):
                break
            if self._inicia_item():
                break
            self._avancar()
        # Marca que, apos sincronizar, e preciso consumir ao menos um token antes
        # de registrar um novo erro (evita cascata de erros sobre o mesmo ponto).
        self.consumiu_desde_sync = False

    def _inicia_declaracao(self):
        return self._e_tipo("PALAVRA_RESERVADA") and self._e_lexema(*TIPOS)

    def _inicia_comando(self):
        return self._e_tipo("IDENTIFICADOR") or self._e_lexema("if") or self._e_lexema("{")

    def _inicia_item(self):
        return self._inicia_declaracao() or self._inicia_comando()

    # ------------------------------------------------------------------
    # programa = { item } FIM
    # ------------------------------------------------------------------

    def _programa(self):
        filhos = []
        while not self._fim():
            if self.limite_atingido:
                break
            marca = self.pos
            try:
                no = self._item()
                self._expandir(filhos, no)
            except _ErroSintatico as exc:
                self._tratar_erro(exc)
            # Garante progresso mesmo que a recuperacao nao tenha avancado.
            if self.pos == marca and not self._fim():
                self._avancar()

        self.contador += 1
        if filhos:
            ti = filhos[0][1]["tokenInicio"]
            tf = filhos[-1][1]["tokenFim"]
            linha, coluna = self.tokens[ti]["linha"], self.tokens[ti]["coluna"]
            tfim = self.tokens[tf]
            linha_fim, coluna_fim = tfim["linha"], tfim["coluna"] + len(tfim["lexema"]) - 1
        else:
            ti = tf = None
            linha = coluna = linha_fim = coluna_fim = 1
        for papel, filho in filhos:
            filho["papel"] = papel
        return {
            "id": self.contador,
            "ordem": self.contador,
            "tipo": "PROGRAMA",
            "rotulo": "Programa",
            "regra": "programa",
            "papel": None,
            "linha": linha,
            "coluna": coluna,
            "linhaFim": linha_fim,
            "colunaFim": coluna_fim,
            "tokenInicio": ti,
            "tokenFim": tf,
            "atributos": {},
            "filhos": [filho for _, filho in filhos],
        }

    def _tratar_erro(self, exc):
        if not self.consumiu_desde_sync:
            # Ainda nao houve progresso desde a ultima sincronizacao: nao registra
            # um novo erro para nao gerar cascata; apenas sincroniza de novo.
            self._sincronizar()
            return
        if len(self.erros) < MAX_ERROS:
            self._registrar(exc.erro)
            if len(self.erros) >= MAX_ERROS:
                self.erros.append({
                    "tipo": "ERRO_SINTATICO",
                    "linha": exc.erro["linha"],
                    "coluna": exc.erro["coluna"],
                    "encontrado": "",
                    "esperado": [],
                    "regra": "",
                    "mensagem": (
                        f"A análise foi interrompida: há mais de {MAX_ERROS} erros "
                        "sintáticos. Corrija os primeiros e analise novamente."
                    ),
                })
                self.limite_atingido = True
        self._sincronizar()

    # ------------------------------------------------------------------
    # item = declaracao | comando
    # ------------------------------------------------------------------

    def _item(self):
        if self._inicia_declaracao():
            return self._declaracao()
        if self._e_tipo("IDENTIFICADOR"):
            return self._atribuicao()
        if self._e_lexema("if"):
            return self._condicional()
        if self._e_lexema("{"):
            return self._bloco()
        self._erro_inicio_item()

    def _erro_inicio_item(self):
        """Erro quando um token nao pode iniciar um item."""
        token = self._atual()
        if token is None:
            self._erro([], REGRA_ITEM, "era esperado um comando ou uma declaração, mas o código terminou")
        lexema = token["lexema"]
        if lexema == "else":
            self._erro(
                [], REGRA_CONDICIONAL,
                "foi encontrado 'else' sem um 'if' correspondente antes dele",
            )
        if lexema == "}":
            self._erro(
                [], REGRA_BLOCO,
                "foi encontrado '}' (chave de fechamento) sem um bloco aberto correspondente",
            )
        if token["tipo"] in ("LITERAL_INTEIRO", "LITERAL_REAL"):
            self._erro(
                [], REGRA_ITEM,
                f"um comando não pode começar com o número '{lexema}'; "
                "um comando começa com um identificador, 'if' ou '{'",
            )
        self._erro(
            [], REGRA_ITEM,
            f"'{lexema}' não inicia uma declaração nem um comando válido",
        )

    # ------------------------------------------------------------------
    # declaracao = tipo declarador { "," declarador } ";"
    # declarador = IDENTIFICADOR [ "=" expressao ]
    # ------------------------------------------------------------------

    def _declaracao(self):
        tipo_token = self._avancar()           # "int" ou "float"
        tipo_dado = tipo_token["lexema"]
        inicio_decl = self.pos - 1

        declaradores = [self._declarador(tipo_dado, inicio_decl)]
        while self._e_lexema(","):
            self._avancar()
            declaradores.append(self._declarador(tipo_dado, None))

        if not self._e_lexema(";"):
            nome = declaradores[-1]["atributos"]["nome"]
            self._erro(
                [";"], REGRA_DECLARACAO,
                f"era esperado ';' para terminar a declaração de '{nome}', "
                f"mas foi encontrado '{self._encontrado()}'",
            )
        ponto = self.pos                       # indice do ";"
        self._avancar()                        # consome ";"

        # Com um unico declarador, a posicao da declaracao vai ate o ";".
        # Com varios, cada declarador para no seu ultimo token e o ";" fica fora.
        if len(declaradores) == 1:
            no = declaradores[0]
            no["tokenFim"] = ponto
            tf = self.tokens[ponto]
            no["linhaFim"] = tf["linha"]
            no["colunaFim"] = tf["coluna"] + len(tf["lexema"]) - 1
            return no

        return _ListaDeclaradores(declaradores)

    def _declarador(self, tipo_dado, inicio_decl):
        if not self._e_tipo("IDENTIFICADOR"):
            self._erro_nome_invalido()
        nome_token = self._avancar()
        nome = nome_token["lexema"]
        inicio = inicio_decl if inicio_decl is not None else self.pos - 1
        atributos = {"tipoDado": tipo_dado, "nome": nome}

        filhos = []
        fim = self.pos - 1                     # ultimo token ate agora: o nome
        if self._e_lexema("="):
            self._avancar()
            valor = self._expressao()
            filhos.append(("valor", valor))
            fim = valor["tokenFim"]

        return self._no("DECLARACAO_VARIAVEL", "declarador", atributos, filhos, inicio, fim)

    def _erro_nome_invalido(self):
        token = self._atual()
        if token is not None and token["tipo"] == "PALAVRA_RESERVADA":
            self._erro(
                ["IDENTIFICADOR"], REGRA_DECLARADOR,
                f"era esperado um identificador para o nome da variável, mas '{token['lexema']}' "
                "é uma palavra reservada e não pode ser nome de variável",
            )
        self._erro(
            ["IDENTIFICADOR"], REGRA_DECLARADOR,
            f"era esperado um identificador para o nome da variável, mas foi encontrado "
            f"'{self._encontrado()}'",
        )

    # ------------------------------------------------------------------
    # atribuicao = IDENTIFICADOR "=" expressao ";"
    # ------------------------------------------------------------------

    def _atribuicao(self):
        nome_token = self._avancar()
        inicio = self.pos - 1
        nome = nome_token["lexema"]

        if not self._e_lexema("="):
            self._erro(
                ["="], REGRA_ATRIBUICAO,
                f"era esperado '=' para atribuir um valor a '{nome}', mas foi encontrado "
                f"'{self._encontrado()}'",
            )
        self._avancar()
        valor = self._expressao()

        if not self._e_lexema(";"):
            self._erro(
                [";"], REGRA_ATRIBUICAO,
                f"era esperado ';' para terminar a atribuição de '{nome}', mas foi encontrado "
                f"'{self._encontrado()}'",
            )
        ponto = self.pos
        self._avancar()

        atributos = {"nome": nome}
        return self._no("ATRIBUICAO", "atribuicao", atributos, [("valor", valor)], inicio, ponto)

    # ------------------------------------------------------------------
    # condicional = "if" "(" expressao ")" bloco [ "else" ( bloco | condicional ) ]
    # ------------------------------------------------------------------

    def _condicional(self):
        inicio = self.pos
        self._avancar()                        # "if"

        if not self._e_lexema("("):
            self._erro(
                ["("], REGRA_CONDICIONAL,
                f"era esperado '(' para abrir a condição do if, mas foi encontrado "
                f"'{self._encontrado()}'",
            )
        self._avancar()
        condicao = self._expressao()
        if not self._e_lexema(")"):
            self._erro(
                [")"], REGRA_CONDICIONAL,
                f"era esperado ')' para fechar a condição do if, mas foi encontrado "
                f"'{self._encontrado()}'",
            )
        self._avancar()

        if not self._e_lexema("{"):
            self._erro(
                ["{"], REGRA_CONDICIONAL,
                "o corpo do if precisa de um bloco entre chaves; era esperado '{', mas foi "
                f"encontrado '{self._encontrado()}'",
            )
        entao = self._bloco()

        filhos = [("condicao", condicao), ("entao", entao)]
        tem_senao = False
        fim = entao["tokenFim"]
        if self._e_lexema("else"):
            tem_senao = True
            self._avancar()
            if self._e_lexema("if"):
                senao = self._profundo(self._condicional)   # else if
            elif self._e_lexema("{"):
                senao = self._bloco()
            else:
                self._erro(
                    ["{", "if"], REGRA_CONDICIONAL,
                    "depois de 'else' era esperado um bloco '{' ou um 'if', mas foi encontrado "
                    f"'{self._encontrado()}'",
                )
            filhos.append(("senao", senao))
            fim = senao["tokenFim"]

        no = self._no("CONDICIONAL", "condicional", {"temSenao": tem_senao}, filhos, inicio, fim)
        return no

    # ------------------------------------------------------------------
    # bloco = "{" { item } "}"
    # ------------------------------------------------------------------

    def _bloco(self):
        self.profundidade += 1
        self._verificar_profundidade()
        inicio = self.pos
        abertura = self._atual()
        self._avancar()                        # "{"

        filhos = []
        while not self._fim() and not self._e_lexema("}"):
            if self.limite_atingido:
                break
            marca = self.pos
            try:
                no = self._item()
                self._expandir(filhos, no)
            except _ErroSintatico as exc:
                self._tratar_erro(exc)
            if self.pos == marca and not self._fim() and not self._e_lexema("}"):
                self._avancar()

        if not self._e_lexema("}"):
            self._erro(
                ["}"], REGRA_BLOCO,
                f"era esperado '}}' para fechar o bloco aberto na linha {abertura['linha']}, "
                f"mas o código terminou" if self._fim() else
                f"era esperado '}}' para fechar o bloco aberto na linha {abertura['linha']}, "
                f"mas foi encontrado '{self._encontrado()}'",
            )
        fim = self.pos
        self._avancar()                        # "}"
        self.profundidade -= 1

        no = self._no("BLOCO", "bloco", {}, filhos, inicio, fim)
        return no

    def _expandir(self, filhos, no):
        """Anexa um no de item, expandindo listas de declaradores em varios itens."""
        if isinstance(no, _ListaDeclaradores):
            for decl in no.nos:
                filhos.append(("item", decl))
        else:
            filhos.append(("item", no))

    # ------------------------------------------------------------------
    # expressao = aditiva [ op_relacional aditiva ]
    # ------------------------------------------------------------------

    def _expressao(self):
        esquerda = self._aditiva()
        if self._e_lexema(*OP_RELACIONAL):
            operador = self._avancar()["lexema"]
            direita = self._aditiva()
            no = self._no(
                "COMPARACAO", "expressao", {"operador": operador},
                [("esquerda", esquerda), ("direita", direita)],
                esquerda["tokenInicio"], direita["tokenFim"],
            )
            if self._e_lexema(*OP_RELACIONAL):
                self._erro(
                    [], REGRA_EXPRESSAO,
                    "comparações encadeadas (como 'a < b < c') não fazem parte do subconjunto; "
                    "use apenas uma comparação por expressão",
                )
            return no
        return esquerda

    # aditiva = multiplicativa { ( "+" | "-" ) multiplicativa }
    def _aditiva(self):
        esquerda = self._multiplicativa()
        while self._e_lexema(*OP_ADITIVO):
            operador = self._avancar()["lexema"]
            direita = self._multiplicativa()
            tipo = "ADICAO" if operador == "+" else "SUBTRACAO"
            esquerda = self._no(
                tipo, "aditiva", {"operador": operador},
                [("esquerda", esquerda), ("direita", direita)],
                esquerda["tokenInicio"], direita["tokenFim"],
            )
        return esquerda

    # multiplicativa = unaria { ( "*" | "/" ) unaria }
    def _multiplicativa(self):
        esquerda = self._unaria()
        while self._e_lexema(*OP_MULTIPLICATIVO):
            operador = self._avancar()["lexema"]
            direita = self._unaria()
            tipo = "MULTIPLICACAO" if operador == "*" else "DIVISAO"
            esquerda = self._no(
                tipo, "multiplicativa", {"operador": operador},
                [("esquerda", esquerda), ("direita", direita)],
                esquerda["tokenInicio"], direita["tokenFim"],
            )
        return esquerda

    # unaria = "-" unaria | primaria
    def _unaria(self):
        if self._e_lexema("-"):
            inicio = self.pos
            self.profundidade += 1
            self._verificar_profundidade()
            self._avancar()
            operando = self._unaria()
            self.profundidade -= 1
            return self._no(
                "NEGACAO", "unaria", {"operador": "-"},
                [("operando", operando)], inicio, operando["tokenFim"],
            )
        return self._primaria()

    # primaria = IDENTIFICADOR | LITERAL_INTEIRO | LITERAL_REAL | "(" expressao ")"
    def _primaria(self):
        token = self._atual()
        if token is None:
            self._erro(
                ["IDENTIFICADOR", "LITERAL_INTEIRO", "LITERAL_REAL", "(", "-"], REGRA_PRIMARIA,
                "era esperado um operando (um identificador, um número, '(' ou '-'), "
                "mas o código terminou",
            )
        tipo = token["tipo"]
        if tipo == "IDENTIFICADOR":
            self._avancar()
            indice = self.pos - 1
            return self._no("IDENTIFICADOR", "primaria", {"nome": token["lexema"]}, [], indice, indice)
        if tipo == "LITERAL_INTEIRO":
            self._avancar()
            indice = self.pos - 1
            return self._no("LITERAL_INTEIRO", "primaria", {"valor": token["lexema"]}, [], indice, indice)
        if tipo == "LITERAL_REAL":
            self._avancar()
            indice = self.pos - 1
            return self._no("LITERAL_REAL", "primaria", {"valor": token["lexema"]}, [], indice, indice)
        if token["lexema"] == "(":
            self.profundidade += 1
            self._verificar_profundidade()
            self._avancar()
            interna = self._expressao()
            if not self._e_lexema(")"):
                self._erro(
                    [")"], REGRA_PRIMARIA,
                    "era esperado ')' para fechar a expressão entre parênteses, mas foi "
                    f"encontrado '{self._encontrado()}'",
                )
            self._avancar()
            self.profundidade -= 1
            return interna
        # Nenhuma alternativa de primaria: falta um operando.
        self._erro(
            ["IDENTIFICADOR", "LITERAL_INTEIRO", "LITERAL_REAL", "(", "-"], REGRA_PRIMARIA,
            f"era esperado um operando (um identificador, um número, '(' ou '-'), mas foi "
            f"encontrado '{token['lexema']}'",
        )

    # ------------------------------------------------------------------
    # Limite de aninhamento
    # ------------------------------------------------------------------

    def _profundo(self, funcao):
        """Executa funcao contando um nivel de aninhamento (para else if)."""
        self.profundidade += 1
        self._verificar_profundidade()
        resultado = funcao()
        self.profundidade -= 1
        return resultado

    def _verificar_profundidade(self):
        if self.profundidade > MAX_PROFUNDIDADE:
            self._erro(
                [], REGRA_EXPRESSAO,
                f"o aninhamento excede o limite de {MAX_PROFUNDIDADE} níveis",
            )


class _ListaDeclaradores:
    """Resultado interno de uma declaracao com varios declaradores.

    O parser devolve este marcador para que _programa e _bloco expandam os
    declaradores em itens irmaos. Nao e exposto na AST.
    """

    def __init__(self, nos):
        self.nos = nos
