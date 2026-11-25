"""Geração de código intermediário a partir da AST do MiniC.

Produz três representações equivalentes da mesma sequência de instruções:
código de três endereços, quádruplas e triplas. A AST é percorrida em pós-ordem,
da esquerda para a direita; cada operação gera um temporário novo (_t1, _t2, ...),
e os desvios usam rótulos sequenciais (L1, L2, ...).

A função pública é gerar_intermediario(ast). Só deve ser chamada quando a análise
sintática teve sucesso (ast não nula). Não há análise semântica: a geração apenas
reflete a estrutura reconhecida pelo parser.
"""

# Símbolo de cada operação binária aritmética.
OP_BINARIO = {
    "ADICAO": "+",
    "SUBTRACAO": "-",
    "MULTIPLICACAO": "*",
    "DIVISAO": "/",
}


def gerar_intermediario(ast):
    """Retorna {"tres_enderecos": [...], "quadruplas": [...], "triplas": [...]}.

    As três listas têm o mesmo tamanho e a mesma ordem: a posição i descreve a
    mesma instrução nas três formas, e cada item guarda o id do nó da AST que a
    gerou (campo "no").
    """
    gerador = _Gerador()
    gerador.percorrer(ast)
    return gerador.montar()


class _Gerador:
    def __init__(self):
        self.instrucoes = []   # instrucoes internas, viram as tres formas no fim
        self.n_temp = 0
        self.n_rotulo = 0

    # ------------------------------------------------------------------
    # Estado auxiliar
    # ------------------------------------------------------------------

    def _novo_temp(self):
        self.n_temp += 1
        return f"_t{self.n_temp}"

    def _novo_rotulo(self):
        self.n_rotulo += 1
        return f"L{self.n_rotulo}"

    def _emitir(self, instrucao):
        self.instrucoes.append(instrucao)

    @staticmethod
    def _filho(no, papel):
        for filho in no["filhos"]:
            if filho["papel"] == papel:
                return filho
        return None

    # ------------------------------------------------------------------
    # Percurso da AST (pós-ordem). Retorna o operando (temp ou valor direto)
    # para nós de expressão; None para comandos e declarações.
    # ------------------------------------------------------------------

    def percorrer(self, no):
        if no is None:
            return None
        tipo = no["tipo"]
        metodo = getattr(self, "_" + tipo.lower(), None)
        if metodo is None:
            return None
        return metodo(no)

    def _programa(self, no):
        for item in no["filhos"]:
            self.percorrer(item)
        return None

    def _bloco(self, no):
        for item in no["filhos"]:
            self.percorrer(item)
        return None

    # Operandos diretos (não geram instrução).
    def _literal_inteiro(self, no):
        return no["atributos"]["valor"]

    def _literal_real(self, no):
        return no["atributos"]["valor"]

    def _identificador(self, no):
        return no["atributos"]["nome"]

    # Operações binárias aritméticas.
    def _binaria(self, no, operador):
        arg1 = self.percorrer(no["filhos"][0])
        arg2 = self.percorrer(no["filhos"][1])
        destino = self._novo_temp()
        self._emitir({"kind": "bin", "op": operador, "arg1": arg1, "arg2": arg2,
                      "res": destino, "no": no["id"]})
        return destino

    def _adicao(self, no):
        return self._binaria(no, OP_BINARIO["ADICAO"])

    def _subtracao(self, no):
        return self._binaria(no, OP_BINARIO["SUBTRACAO"])

    def _multiplicacao(self, no):
        return self._binaria(no, OP_BINARIO["MULTIPLICACAO"])

    def _divisao(self, no):
        return self._binaria(no, OP_BINARIO["DIVISAO"])

    def _comparacao(self, no):
        return self._binaria(no, no["atributos"]["operador"])

    def _negacao(self, no):
        arg1 = self.percorrer(no["filhos"][0])
        destino = self._novo_temp()
        self._emitir({"kind": "unary", "op": "minus", "arg1": arg1,
                      "res": destino, "no": no["id"]})
        return destino

    # Declaração e atribuição: calculam a expressão e geram uma cópia.
    def _declaracao_variavel(self, no):
        valor = self._filho(no, "valor")
        if valor is None:
            return None   # declaração sem inicialização não gera instrução
        operando = self.percorrer(valor)
        self._emitir({"kind": "copy", "res": no["atributos"]["nome"],
                      "arg1": operando, "no": no["id"]})
        return None

    def _atribuicao(self, no):
        operando = self.percorrer(self._filho(no, "valor"))
        self._emitir({"kind": "copy", "res": no["atributos"]["nome"],
                      "arg1": operando, "no": no["id"]})
        return None

    def _condicional(self, no):
        condicao = self.percorrer(self._filho(no, "condicao"))
        l1 = self._novo_rotulo()
        self._emitir({"kind": "if_false", "arg1": condicao, "label": l1, "no": no["id"]})
        self.percorrer(self._filho(no, "entao"))

        senao = self._filho(no, "senao")
        if senao is not None:
            l2 = self._novo_rotulo()
            self._emitir({"kind": "goto", "label": l2, "no": no["id"]})
            self._emitir({"kind": "label", "label": l1, "no": no["id"]})
            self.percorrer(senao)
            self._emitir({"kind": "label", "label": l2, "no": no["id"]})
        else:
            self._emitir({"kind": "label", "label": l1, "no": no["id"]})
        return None

    # ------------------------------------------------------------------
    # Montagem das três formas
    # ------------------------------------------------------------------

    def montar(self):
        # Mapas para as triplas: temporário -> número da instrução que o definiu,
        # e rótulo -> número da instrução do rótulo (destino dos desvios).
        def_temp = {}
        def_rotulo = {}
        for i, ins in enumerate(self.instrucoes, start=1):
            if ins["kind"] in ("bin", "unary"):
                def_temp[ins["res"]] = i
            elif ins["kind"] == "label":
                def_rotulo[ins["label"]] = i

        def ref(valor):
            """Nas triplas, um temporário vira (n), referência à instrução n."""
            if valor in def_temp:
                return f"({def_temp[valor]})"
            return valor

        tres = []
        quad = []
        trip = []
        for i, ins in enumerate(self.instrucoes, start=1):
            tres.append({"texto": self._texto(ins), "no": ins["no"]})
            quad.append(self._quadrupla(ins))
            trip.append(self._tripla(ins, i, ref, def_rotulo))
        return {"tres_enderecos": tres, "quadruplas": quad, "triplas": trip}

    @staticmethod
    def _texto(ins):
        k = ins["kind"]
        if k == "bin":
            return f"{ins['res']} = {ins['arg1']} {ins['op']} {ins['arg2']}"
        if k == "unary":
            return f"{ins['res']} = minus {ins['arg1']}"
        if k == "copy":
            return f"{ins['res']} = {ins['arg1']}"
        if k == "if_false":
            return f"if_false {ins['arg1']} goto {ins['label']}"
        if k == "goto":
            return f"goto {ins['label']}"
        if k == "label":
            return f"label {ins['label']}"
        return ""

    @staticmethod
    def _quadrupla(ins):
        k = ins["kind"]
        if k == "bin":
            q = (ins["op"], ins["arg1"], ins["arg2"], ins["res"])
        elif k == "unary":
            q = ("minus", ins["arg1"], None, ins["res"])
        elif k == "copy":
            q = ("=", ins["arg1"], None, ins["res"])
        elif k == "if_false":
            q = ("if_false", ins["arg1"], None, ins["label"])
        elif k == "goto":
            q = ("goto", None, None, ins["label"])
        elif k == "label":
            q = ("label", None, None, ins["label"])
        else:
            q = ("", None, None, None)
        return {"op": q[0], "arg1": q[1], "arg2": q[2], "resultado": q[3], "no": ins["no"]}

    @staticmethod
    def _tripla(ins, numero, ref, def_rotulo):
        k = ins["kind"]
        if k == "bin":
            t = (ins["op"], ref(ins["arg1"]), ref(ins["arg2"]))
        elif k == "unary":
            t = ("minus", ref(ins["arg1"]), None)
        elif k == "copy":
            t = ("=", ins["res"], ref(ins["arg1"]))
        elif k == "if_false":
            t = ("if_false", ref(ins["arg1"]), def_rotulo.get(ins["label"]))
        elif k == "goto":
            t = ("goto", def_rotulo.get(ins["label"]), None)
        elif k == "label":
            t = ("label", ins["label"], None)
        else:
            t = ("", None, None)
        return {"numero": numero, "op": t[0], "arg1": t[1], "arg2": t[2], "no": ins["no"]}
