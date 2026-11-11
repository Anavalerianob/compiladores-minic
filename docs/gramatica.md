# Gramática do MiniC

Este documento descreve a gramática do subconjunto MiniC reconhecida pelo parser da etapa 4. A gramática é a mesma implementada em `backend/parser.py`.

## Gramática em EBNF

```
programa        = { item } FIM ;
item            = declaracao | comando ;
declaracao      = tipo declarador { "," declarador } ";" ;
declarador      = IDENTIFICADOR [ "=" expressao ] ;
tipo            = "int" | "float" ;
comando         = atribuicao | condicional | bloco ;
atribuicao      = IDENTIFICADOR "=" expressao ";" ;
condicional     = "if" "(" expressao ")" bloco [ "else" ( bloco | condicional ) ] ;
bloco           = "{" { item } "}" ;
expressao       = aditiva [ op_relacional aditiva ] ;
op_relacional   = "==" | "!=" | "<" | "<=" | ">" | ">=" ;
aditiva         = multiplicativa { ( "+" | "-" ) multiplicativa } ;
multiplicativa  = unaria { ( "*" | "/" ) unaria } ;
unaria          = "-" unaria | primaria ;
primaria        = IDENTIFICADOR | LITERAL_INTEIRO | LITERAL_REAL | "(" expressao ")" ;
```

## Símbolo inicial, terminais e não terminais

O símbolo inicial é `programa`. `FIM` representa o fim da lista de tokens: não é um token produzido pelo scanner, e sim a ausência de mais tokens.

Não terminais: `programa`, `item`, `declaracao`, `declarador`, `tipo`, `comando`, `atribuicao`, `condicional`, `bloco`, `expressao`, `op_relacional`, `aditiva`, `multiplicativa`, `unaria` e `primaria`.

Terminais: as palavras reservadas `int`, `float`, `if` e `else`; as categorias `IDENTIFICADOR`, `LITERAL_INTEIRO` e `LITERAL_REAL`; os operadores `+ - * / = == != < <= > >=`; e os delimitadores `( ) { } ; ,`.

## Correspondência com as categorias do scanner

O parser consome os tokens que o scanner já produziu e não altera o scanner. Cada terminal da gramática corresponde a um token assim:

| Terminal da gramática | Token do scanner |
|---|---|
| `int`, `float`, `if`, `else` | `PALAVRA_RESERVADA` com esse lexema |
| `IDENTIFICADOR` | token da categoria `IDENTIFICADOR` |
| `LITERAL_INTEIRO` | token da categoria `LITERAL_INTEIRO` |
| `LITERAL_REAL` | token da categoria `LITERAL_REAL` |
| `+ - * / = == != < <= > >=` | `OPERADOR` com esse lexema |
| `( ) { } ; ,` | `DELIMITADOR` com esse lexema |

Nenhum token novo foi necessário, então o scanner continuou igual ao da etapa 3.

## Precedência e associatividade

A gramática expressa a precedência pela forma como as regras se encadeiam. Da menor para a maior precedência:

1. operadores relacionais (`==`, `!=`, `<`, `<=`, `>`, `>=`);
2. adição e subtração (`+`, `-`);
3. multiplicação e divisão (`*`, `/`);
4. menos unário (`-`);
5. parênteses.

A associatividade de `+`, `-`, `*` e `/` é à esquerda: as repetições `{ }` das regras `aditiva` e `multiplicativa` constroem a árvore da esquerda para a direita. Os operadores relacionais não são associativos: a regra `expressao` permite no máximo uma comparação, então `a < b < c` é um erro sintático.

### Exemplos de precedência e a AST de cada um

`int resultado = 10 + 5 * 2;`

A multiplicação tem precedência maior que a adição, então ela fica abaixo na árvore:

```
DECLARACAO_VARIAVEL (int resultado)
└── ADICAO (+)
    ├── LITERAL_INTEIRO 10
    └── MULTIPLICACAO (*)
        ├── LITERAL_INTEIRO 5
        └── LITERAL_INTEIRO 2
```

`int r = 20 - 5 - 3;`

A subtração é associativa à esquerda, então `(20 - 5) - 3`:

```
SUBTRACAO (-)
├── SUBTRACAO (-)
│   ├── LITERAL_INTEIRO 20
│   └── LITERAL_INTEIRO 5
└── LITERAL_INTEIRO 3
```

`int m = (10 + 5) * 2;`

Os parênteses mudam a ordem: a adição passa a ser filha da multiplicação. Os parênteses não geram nó:

```
MULTIPLICACAO (*)
├── ADICAO (+)
│   ├── LITERAL_INTEIRO 10
│   └── LITERAL_INTEIRO 5
└── LITERAL_INTEIRO 2
```

## Construções suportadas

1. declaração de variáveis `int` e `float`, com inicialização opcional e lista de declaradores separada por vírgula;
2. atribuição a uma variável;
3. expressões com os operadores aritméticos e relacionais, menos unário e parênteses;
4. condicional `if`, com `else` e `else if` opcionais, sempre com blocos entre chaves;
5. blocos entre chaves, que podem conter declarações e comandos aninhados.

## Construções fora do escopo

Não fazem parte do subconjunto: laços (`while`, `for`), funções, `return`, operadores lógicos (`&&`, `||`, `!`), strings, vetores, ponteiros, incremento (`++`), atribuições compostas (`+=`), declaração sem tipo e `if` sem chaves. Os elementos que o scanner já rejeita continuam como erro léxico. O `if` e o `else` exigem bloco com chaves, o que evita a ambiguidade do else pendente; `else if` é permitido pela alternativa `condicional` da regra do `else`.

A gramática não tem recursão à esquerda e precisa de apenas um token de olhar à frente (é LL(1)): em `item`, uma palavra reservada `int` ou `float` inicia uma declaração; um `IDENTIFICADOR`, um `if` ou um `{` iniciam um comando.

## Exemplos válidos

```
int x;
int a, b = 2;
float media = 3.5;
x = -a * 2;
if (a <= b) { a = 1; } else if (a > 0) { b = 2; } else { b = 3; }
```

Um programa vazio (sem tokens) é válido: a análise sintática não gera erro e a AST tem apenas o nó `PROGRAMA`.

## Exemplos inválidos

As mensagens abaixo foram copiadas de uma execução real do parser.

| Entrada | Mensagem do parser |
|---|---|
| `int x = 5` | Erro sintático na linha 1, coluna 10: era esperado ';' para terminar a declaração de 'x', mas foi encontrado 'fim do código'. |
| `if (a < b < c) { }` | Erro sintático na linha 1, coluna 11: comparações encadeadas (como 'a < b < c') não fazem parte do subconjunto; use apenas uma comparação por expressão. |
| `x = 1 + * 2;` | Erro sintático na linha 1, coluna 9: era esperado um operando (um identificador, um número, '(' ou '-'), mas foi encontrado '*'. |
| `int if = 3;` | Erro sintático na linha 1, coluna 5: era esperado um identificador para o nome da variável, mas 'if' é uma palavra reservada e não pode ser nome de variável. |

O formato dos nós da AST e a tabela completa de tipos estão em `ast.md`.
