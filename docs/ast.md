# Árvore sintática abstrata (AST)

Este documento descreve o formato da AST que o parser devolve ao frontend. A gramática está em `gramatica.md`.

## Formato do nó

Todo nó da AST segue o mesmo formato:

```json
{
  "id": 4,
  "ordem": 4,
  "tipo": "MULTIPLICACAO",
  "rotulo": "Multiplicação (*)",
  "regra": "multiplicativa",
  "papel": "direita",
  "linha": 1, "coluna": 22, "linhaFim": 1, "colunaFim": 26,
  "tokenInicio": 5, "tokenFim": 7,
  "atributos": { "operador": "*" },
  "filhos": [ ... ]
}
```

| Campo | Significado |
|---|---|
| `id` | inteiro único no programa, igual a `ordem` |
| `ordem` | ordem de criação do nó, começando em 1, em pós-ordem (os filhos antes do pai); é o que o passo a passo usa |
| `tipo` | tipo do nó (ver tabela abaixo) |
| `rotulo` | texto do nó para a árvore, como "Adição (+)" ou "Literal inteiro: 10" |
| `regra` | nome do não terminal da gramática que reconheceu o nó |
| `papel` | função do nó em relação ao pai; `null` na raiz |
| `linha`, `coluna` | primeiro caractere do primeiro token do nó |
| `linhaFim`, `colunaFim` | último caractere do último token do nó (inclusivo) |
| `tokenInicio`, `tokenFim` | índices (base 0) na lista de tokens do scanner, inclusivos |
| `atributos` | dados próprios do nó (operador, nome, valor, tipoDado, temSenao) |
| `filhos` | lista de nós filhos |

Os valores possíveis de `papel` são: `item`, `tipo`, `valor`, `esquerda`, `direita`, `operando`, `condicao`, `entao` e `senao`.

## Tabela de tipos de nó

| `tipo` | `atributos` | filhos (papel) |
|---|---|---|
| `PROGRAMA` | `{}` | itens (`item`) |
| `DECLARACAO_VARIAVEL` | `{"tipoDado": "int" ou "float", "nome": "x"}` | inicialização opcional (`valor`) |
| `ATRIBUICAO` | `{"nome": "x"}` | expressão (`valor`) |
| `CONDICIONAL` | `{"temSenao": bool}` | condição (`condicao`), bloco (`entao`), bloco ou `CONDICIONAL` (`senao`) |
| `BLOCO` | `{}` | itens (`item`) |
| `ADICAO`, `SUBTRACAO`, `MULTIPLICACAO`, `DIVISAO` | `{"operador": "+"}` etc. | esquerda (`esquerda`), direita (`direita`) |
| `COMPARACAO` | `{"operador": "<="}` etc. | esquerda (`esquerda`), direita (`direita`) |
| `NEGACAO` | `{"operador": "-"}` | operando (`operando`) |
| `IDENTIFICADOR` | `{"nome": "x"}` | nenhum |
| `LITERAL_INTEIRO`, `LITERAL_REAL` | `{"valor": "10"}` (texto do lexema) | nenhum |

Os parênteses não geram nó: apenas alteram a organização da árvore. A AST não guarda `;` nem as chaves. A posição de `DECLARACAO_VARIAVEL` e de `ATRIBUICAO` vai até o `;`. A exceção é a lista de declaradores: em `int a, b = 2;`, cada declarador gera um nó com o mesmo `tipoDado`; o primeiro vai do `int` até `a`, o segundo de `b` até `2`, e o `;` fica fora dos dois.

## Posições e ordem de criação

As posições vêm dos tokens. `linha` e `coluna` são as do primeiro token do nó; `linhaFim` e `colunaFim` são o último caractere do último token. `tokenInicio` e `tokenFim` são os índices na lista do scanner.

O campo `ordem` reflete a ordem em que o parser criou os nós, em pós-ordem. Para `int resultado = 10 + 5 * 2;`, a ordem de criação é: `10`, `5`, `2`, `MULTIPLICACAO`, `ADICAO`, `DECLARACAO_VARIAVEL`, `PROGRAMA`. O passo a passo da interface usa essa ordem para mostrar a árvore sendo construída dos filhos para o pai.

## Exemplo completo

A AST abaixo foi gerada executando o parser sobre `int resultado = 10 + 5 * 2;` e conferida com a referência do enunciado. Os tokens são: `int` (0), `resultado` (1), `=` (2), `10` (3), `+` (4), `5` (5), `*` (6), `2` (7), `;` (8).

```json
{
  "id": 7, "ordem": 7, "tipo": "PROGRAMA", "rotulo": "Programa", "regra": "programa",
  "papel": null, "linha": 1, "coluna": 1, "linhaFim": 1, "colunaFim": 27,
  "tokenInicio": 0, "tokenFim": 8, "atributos": {},
  "filhos": [
    {
      "id": 6, "ordem": 6, "tipo": "DECLARACAO_VARIAVEL", "rotulo": "Declaração: int resultado",
      "regra": "declarador", "papel": "item", "linha": 1, "coluna": 1, "linhaFim": 1, "colunaFim": 27,
      "tokenInicio": 0, "tokenFim": 8, "atributos": { "tipoDado": "int", "nome": "resultado" },
      "filhos": [
        {
          "id": 5, "ordem": 5, "tipo": "ADICAO", "rotulo": "Adição (+)", "regra": "aditiva",
          "papel": "valor", "linha": 1, "coluna": 17, "linhaFim": 1, "colunaFim": 26,
          "tokenInicio": 3, "tokenFim": 7, "atributos": { "operador": "+" },
          "filhos": [
            {
              "id": 1, "ordem": 1, "tipo": "LITERAL_INTEIRO", "rotulo": "Literal inteiro: 10",
              "regra": "primaria", "papel": "esquerda", "linha": 1, "coluna": 17, "linhaFim": 1,
              "colunaFim": 18, "tokenInicio": 3, "tokenFim": 3, "atributos": { "valor": "10" }, "filhos": []
            },
            {
              "id": 4, "ordem": 4, "tipo": "MULTIPLICACAO", "rotulo": "Multiplicação (*)",
              "regra": "multiplicativa", "papel": "direita", "linha": 1, "coluna": 22, "linhaFim": 1,
              "colunaFim": 26, "tokenInicio": 5, "tokenFim": 7, "atributos": { "operador": "*" },
              "filhos": [
                {
                  "id": 2, "ordem": 2, "tipo": "LITERAL_INTEIRO", "rotulo": "Literal inteiro: 5",
                  "regra": "primaria", "papel": "esquerda", "linha": 1, "coluna": 22, "linhaFim": 1,
                  "colunaFim": 22, "tokenInicio": 5, "tokenFim": 5, "atributos": { "valor": "5" }, "filhos": []
                },
                {
                  "id": 3, "ordem": 3, "tipo": "LITERAL_INTEIRO", "rotulo": "Literal inteiro: 2",
                  "regra": "primaria", "papel": "direita", "linha": 1, "coluna": 26, "linhaFim": 1,
                  "colunaFim": 26, "tokenInicio": 7, "tokenFim": 7, "atributos": { "valor": "2" }, "filhos": []
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## Tokens, árvore de derivação e AST

São três estruturas diferentes. A sequência de tokens é o que o scanner reconheceu, em ordem. A árvore de derivação mostraria cada regra da gramática aplicada e todos os terminais, inclusive `;` e os parênteses. A AST guarda só o que importa para o significado do programa: não tem o `;`, não tem as chaves, e os parênteses não viram nó (eles apenas mudam a forma da árvore).

Este projeto exibe a AST e não exibe a árvore de derivação. Isso é uma limitação registrada no README.
