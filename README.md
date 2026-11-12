# MiniC Analisador

Disciplina: ICE0619 Compiladores (UFJ, 2026.2)
Autora: Ana Luísa Valeriano Bomfim

## Objetivo

O MiniC Analisador é um software educacional cujo propósito é realizar a análise léxica, sintática e semântica de programas escritos em um subconjunto da linguagem C, exibindo os resultados em uma interface web, de modo a auxiliar estudantes na compreensão do processo de compilação.

Na versão atual (etapa 4), estão implementados o analisador léxico (scanner) e o analisador sintático (parser), com a construção da árvore sintática abstrata (AST). O sistema permite escrever, colar ou selecionar um programa, enviá-lo ao backend e visualizar os tokens reconhecidos, os erros léxicos com linha e coluna, a execução passo a passo do autômato, a AST navegável com a construção passo a passo e os erros sintáticos citando a regra gramatical violada. Há ainda um diferencial opcional: explicações didáticas geradas por uma IA local (Llama 3.2, pelo Ollama). A análise semântica ainda não foi implementada e será desenvolvida na etapa 5.

A gramática formal está em `docs/gramatica.md` e o formato da AST em `docs/ast.md`.

## Linguagem escolhida e subconjunto previsto

Optou-se pela linguagem C, haja vista que se trata da linguagem utilizada nas disciplinas introdutórias de programação do curso, de modo que seu público-alvo já possui familiaridade com sua sintaxe. Ademais, sua gramática é relativamente regular e amplamente documentada na literatura de compiladores.

O subconjunto previsto (MiniC) abrange:

1. Declaração de variáveis dos tipos `int` e `float`, com inicialização opcional;
2. Atribuição de valores a variáveis;
3. Operadores aritméticos `+`, `-`, `*` e `/`, com uso de parênteses;
4. Operadores relacionais `==`, `!=`, `<`, `<=`, `>` e `>=`;
5. Estrutura condicional `if`/`else`.

Laços de repetição, funções, vetores, ponteiros e structs foram deliberadamente excluídos, porquanto abranger a linguagem inteira de uma só vez tornaria o projeto inviável.

## Escopo léxico

Categorias de tokens reconhecidas:

| Categoria | Regra | Exemplos |
|---|---|---|
| `PALAVRA_RESERVADA` | `int`, `float`, `if`, `else`, com distinção entre maiúsculas e minúsculas (`INT` é identificador) | `int`, `float`, `if`, `else` |
| `IDENTIFICADOR` | `[A-Za-z_][A-Za-z0-9_]*`, somente caracteres ASCII | `numero`, `_x1`, `integer` |
| `LITERAL_INTEIRO` | `[0-9]+` | `0`, `10`, `42` |
| `LITERAL_REAL` | `[0-9]+.[0-9]+` | `3.5`, `0.25` |
| `OPERADOR` | `+ - * / = == != < <= > >=` | `<=`, `==` |
| `DELIMITADOR` | `( ) { } ; ,` | `;`, `{` |

Tratamentos realizados pelo scanner:

| Situação | Tratamento |
|---|---|
| Espaço, tabulação, `\r` e `\n` | Ignorados. `\n` incrementa a linha e retorna a coluna para 1; a tabulação conta como uma coluna. Linha e coluna começam em 1. |
| Comentário de linha (`//` até o fim da linha) | Ignorado, inclusive quando contém caracteres fora do subconjunto. |
| Comentário de bloco (`/* ... */`, podendo ocupar várias linhas) | Ignorado; a contagem de linhas continua correta após o comentário. |
| Comentário de bloco não fechado | Erro léxico com lexema `/*`, na posição em que o comentário começa. |
| Operadores de dois caracteres | Regra do maior lexema: `<=` forma um único token, enquanto `= =` (com espaço) forma dois tokens `=`. |
| Caractere fora do subconjunto (`@`, `#`, `$`, `"`, `'`, `&`, `\|`, `.`, letras acentuadas) | Erro léxico cujo lexema é o próprio caractere. |
| `!` isolado (sem `=` em seguida) | Erro léxico com a orientação de que o operador suportado é `!=`. |
| Literal numérico malformado (`3.`, `3.5.2`, `12abc`, `1.2x`) | Um único erro léxico cujo lexema é o trecho inteiro; nenhum token é gerado para esse trecho. |
| Código com erro sintático, mas com tokens válidos (por exemplo, `int = = ; if else )`) | Tokenizado normalmente, sem erros, pois a verificação da estrutura cabe à análise sintática. |

Elementos de C que não fazem parte do subconjunto e comportamento atual do scanner:

| Elemento | Exemplos | Comportamento |
|---|---|---|
| Literais de string e de caractere | `"a"`, `'c'` | As aspas são informadas como erros léxicos, e o conteúdo é reconhecido como identificador |
| Operadores lógicos | `&&`, `\|\|`, `!` | Cada caractere é informado como erro léxico (no caso de `!`, com orientação sobre `!=`) |
| Colchetes | `[`, `]` | Informados como erros léxicos |
| Outras palavras reservadas de C | `while`, `return`, `for` | Reconhecidas como identificadores, pois não pertencem à tabela de palavras reservadas do subconjunto |
| Diretivas de pré-processador | `#include` | O caractere `#` é informado como erro léxico, e `include` é reconhecido como identificador |

Todos os erros são acumulados, e a análise prossegue após cada um deles. A mensagem de cada erro segue o formato `Erro léxico na linha L, coluna C: <descrição>`, como em `Erro léxico na linha 1, coluna 3: caractere não reconhecido '@'. Verifique se ele faz parte do subconjunto suportado.`

## Scanner

O scanner encontra-se em `backend/scanner.py` e foi escrito manualmente em Python, sem geradores como Flex ou ANTLR e sem uma expressão regular de tokenização completa. Optou-se por essa abordagem porque percorrer o código caractere a caractere, simulando um autômato finito determinístico, permite registrar cada transição de estado realizada no reconhecimento de um lexema. Essas transições são enviadas à interface e exibidas no passo a passo didático, algo que um gerador de analisadores ocultaria.

A função pública é `analisar(codigo)`, que retorna `{"tokens": [...], "erros": [...]}`. Cada token contém `tipo`, `lexema`, `linha`, `coluna` e `transicoes`, sendo esta última a lista de transições `{"de", "caractere", "para"}` percorridas. Cada erro contém `tipo` (`ERRO_LEXICO`), `lexema`, `linha`, `coluna` e `mensagem`. O módulo também exporta `PALAVRAS_RESERVADAS`.

Estados do autômato:

| Estado | Significado |
|---|---|
| `inicial` | Início do reconhecimento de um novo lexema |
| `identificador` | Letra ou `_` lido; aceita letras, dígitos e `_` em seguida |
| `inteiro` | Um ou mais dígitos lidos |
| `ponto_decimal` | Dígitos seguidos de `.`; exige ao menos mais um dígito |
| `real` | Dígitos, ponto e dígitos lidos |
| `igual`, `menor`, `maior`, `exclamacao` | Primeiro caractere de `=`, `<`, `>` ou `!`, que pode ser seguido de `=` |
| `barra` | `/` lido; decide entre operador de divisão e início de comentário |
| `operador` | Operador reconhecido (`+`, `-`, `*` ou o segundo caractere de `==`, `!=`, `<=`, `>=`) |
| `delimitador` | Delimitador reconhecido |

Exemplos de caminhos percorridos: `3.5` passa por `inicial`, `inteiro`, `ponto_decimal` e `real`; `<=` passa por `inicial`, `menor` e `operador`; `ab` realiza as transições `inicial --'a'--> identificador` e `identificador --'b'--> identificador`. As palavras reservadas percorrem o mesmo caminho dos identificadores e são distinguidas ao final, pela comparação do lexema com a tabela de palavras reservadas.

A regra do maior lexema é aplicada em todas as categorias: o scanner só encerra um token quando o próximo caractere não pode estender o lexema atual. Por esse motivo, em `12abc` o trecho inteiro é tratado como um único literal malformado, em vez de produzir o inteiro `12` e o identificador `abc`.

A lista de tokens produzida pelo scanner será a entrada do analisador sintático na etapa 4. As posições (linha e coluna) mantidas em cada token permitirão que os erros sintáticos também sejam informados com localização precisa.

### Exemplo de entrada e saída

O exemplo a seguir foi obtido executando o scanner sobre a entrada `if (a <= 2) b = 1.; @`. Para facilitar a leitura, as transições foram omitidas da tabela.

| Tipo | Lexema | Linha | Coluna |
|---|---|---|---|
| `PALAVRA_RESERVADA` | `if` | 1 | 1 |
| `DELIMITADOR` | `(` | 1 | 4 |
| `IDENTIFICADOR` | `a` | 1 | 5 |
| `OPERADOR` | `<=` | 1 | 7 |
| `LITERAL_INTEIRO` | `2` | 1 | 10 |
| `DELIMITADOR` | `)` | 1 | 11 |
| `IDENTIFICADOR` | `b` | 1 | 13 |
| `OPERADOR` | `=` | 1 | 15 |
| `DELIMITADOR` | `;` | 1 | 19 |

Erros retornados:

```
Erro léxico na linha 1, coluna 17: literal numérico malformado '1.'. Um literal real deve ter dígitos depois do ponto (por exemplo, 3.0).
Erro léxico na linha 1, coluna 21: caractere não reconhecido '@'. Verifique se ele faz parte do subconjunto suportado.
```

As transições do token `<=` foram `inicial --'<'--> menor` e `menor --'='--> operador`.

## Parser (análise sintática)

O parser está em `backend/parser.py` e foi escrito à mão como um descendente recursivo, sem ANTLR, Lark ou PLY. Há uma função por não terminal da gramática. Escolhi essa estratégia por ser a mais didática: cada função espelha uma regra da gramática, o que permite registrar a ordem em que os nós são construídos (usada no passo a passo da interface) e citar a regra violada em cada erro. A gramática não tem recursão à esquerda e usa um token de olhar à frente (é LL(1)). A gramática completa, a precedência e os exemplos estão em `docs/gramatica.md`, e o formato da AST em `docs/ast.md`.

A função pública é `analisar_sintaxe(tokens)`, que recebe a lista de tokens do scanner (sem reexecutá-lo) e retorna `{"sucesso": bool, "ast": dict ou None, "erros": [...]}`. Com qualquer erro sintático, `sucesso` é `false` e `ast` é `null`.

Decisão sobre erros léxicos: se o scanner encontra erros léxicos, o parser não é executado, porque tokens faltando produziriam erros sintáticos sem sentido. A resposta informa isso, e a interface explica ao usuário que a análise sintática não foi executada.

Recuperação de erros: o parser usa o modo pânico. Ao encontrar um erro, registra o diagnóstico (com a regra violada, o que era esperado e o que foi encontrado) e descarta tokens até um ponto de sincronização (`;`, `}` ou o início de um item). Não registra um novo erro antes de consumir ao menos um token após a sincronização, o que evita cascata. O limite é de 20 erros por análise.

Limite de aninhamento: parênteses, menos unário, blocos e else if somados são limitados a 100 níveis. Ao passar disso, o parser gera um erro sintático tratado, em vez de deixar a recursão do Python estourar e virar erro 500.

Esta etapa não implementa análise semântica (tabela de símbolos, tipos, variável não declarada); isso é da etapa 5. O parser só verifica a estrutura e constrói a AST.

## Tecnologias utilizadas

1. Frontend: HTML, CSS e JavaScript puro, servidos pelo Nginx;
2. Backend: Python 3.12 com Flask; a comunicação com o Ollama usa apenas `urllib` da biblioteca padrão;
3. IA opcional: Ollama com o modelo Llama 3.2 (3B), em um contêiner próprio;
4. Testes: pytest (backend), node:test com jsdom (frontend) e scripts shell com curl (implantação e IA);
5. Ambiente: Docker e Docker Compose.

A etapa 4 não acrescentou dependências ao backend (Flask e pytest) nem ao frontend (sem bibliotecas externas e sem CDN); a árvore da AST é feita com HTML, CSS e JavaScript puro. A única novidade de infraestrutura é o contêiner do Ollama.

## Estrutura do repositório

```
.
├── backend/
│   ├── app.py               Rotas da API e tratamento de erros
│   ├── scanner.py           Analisador léxico (scanner)
│   ├── parser.py            Analisador sintático (parser) e construção da AST
│   ├── ia.py                Explicações com IA local (Ollama)
│   ├── validacao.py         Validações da entrada recebida
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│       ├── test_api.py      Testes da validação e dos endpoints
│       ├── test_scanner.py  Testes do scanner
│       ├── test_parser.py   Testes do parser e da AST
│       └── test_ia.py       Testes da IA (com mock e integração real pulada)
├── frontend/
│   ├── index.html           Tela principal
│   ├── app.js               Exemplos, validação, comunicação, análise léxica, AST e IA
│   ├── nginx.conf           Servidor web e proxy para o backend
│   ├── package.json         Dependências e comando dos testes
│   ├── Dockerfile
│   └── tests/interface.test.js   Testes de interface
├── tests/
│   ├── implantacao.sh       Teste de implantação
│   └── ia.sh                Teste manual da IA (com os contêineres rodando)
├── docs/
│   ├── gramatica.md         Gramática EBNF, precedência e exemplos
│   ├── ast.md               Formato da AST e exemplo completo
│   ├── fluxograma.md        Fluxogramas do processamento e da IA
│   ├── materiais-e-metodos.md   Decisões técnicas e critérios de avaliação
│   └── testes.md            Registro dos testes executados
├── docker-compose.yml
└── README.md
```

## Arquitetura e comunicação

O sistema é composto por dois serviços. O frontend é servido pelo Nginx na porta 8080, e as requisições destinadas a `/api/` são repassadas pelo próprio Nginx ao serviço `backend` na rede interna do Docker. Por conseguinte, o navegador acessa apenas `http://localhost:8080`, não dependendo de endereços que funcionam somente na máquina de desenvolvimento. O backend possui um mecanismo de verificação de saúde (`/api/saude`), e o frontend só é iniciado depois que o backend estiver saudável.

### Formato da comunicação

Requisição enviada pelo frontend:

```
POST /api/analisar
Content-Type: application/json

{ "codigo": "float x = 3.5;" }
```

Após validar a entrada, o backend executa o scanner e, se não houver erros léxicos, o parser. A resposta abaixo mostra apenas os campos da análise léxica, preservados desde a etapa 3; a etapa 4 acrescenta os blocos `lexico` e `sintatico`, descritos logo a seguir. As chaves são ordenadas alfabeticamente pelo Flask:

```json
{
  "caracteres": 14,
  "erros": [],
  "linhas": 1,
  "mensagem": "Análise léxica e sintática concluídas sem erros: 5 token(s) e 3 nó(s) na AST.",
  "recebido": true,
  "sucesso": true,
  "tokens": [
    {
      "coluna": 1, "lexema": "float", "linha": 1, "tipo": "PALAVRA_RESERVADA",
      "transicoes": [
        { "caractere": "f", "de": "inicial", "para": "identificador" },
        { "caractere": "l", "de": "identificador", "para": "identificador" },
        { "caractere": "o", "de": "identificador", "para": "identificador" },
        { "caractere": "a", "de": "identificador", "para": "identificador" },
        { "caractere": "t", "de": "identificador", "para": "identificador" }
      ]
    },
    {
      "coluna": 7, "lexema": "x", "linha": 1, "tipo": "IDENTIFICADOR",
      "transicoes": [ { "caractere": "x", "de": "inicial", "para": "identificador" } ]
    },
    {
      "coluna": 9, "lexema": "=", "linha": 1, "tipo": "OPERADOR",
      "transicoes": [ { "caractere": "=", "de": "inicial", "para": "igual" } ]
    },
    {
      "coluna": 11, "lexema": "3.5", "linha": 1, "tipo": "LITERAL_REAL",
      "transicoes": [
        { "caractere": "3", "de": "inicial", "para": "inteiro" },
        { "caractere": ".", "de": "inteiro", "para": "ponto_decimal" },
        { "caractere": "5", "de": "ponto_decimal", "para": "real" }
      ]
    },
    {
      "coluna": 14, "lexema": ";", "linha": 1, "tipo": "DELIMITADOR",
      "transicoes": [ { "caractere": ";", "de": "inicial", "para": "delimitador" } ]
    }
  ]
}
```

Quando há erros léxicos, o campo `sucesso` vale `false`, a lista `erros` contém um objeto por erro e a mensagem passa a ser, por exemplo, `Análise léxica concluída com 1 erro(s) léxico(s) e 6 token(s) reconhecido(s). A análise sintática não foi executada.` (resposta para `int a = 5 @ 2;`). O campo `sucesso` do topo continua se referindo à análise léxica.

### Contrato da etapa 4

A resposta 200 de `POST /api/analisar` preserva todos os campos do topo da etapa 3 (`recebido`, `sucesso`, `mensagem`, `linhas`, `caracteres`, `tokens`, `erros`), que seguem se referindo à análise léxica. A etapa 4 acrescenta dois blocos:

```json
{
  "lexico":    { "sucesso": true, "tokens": [ ... ], "erros": [] },
  "sintatico": { "executado": true, "sucesso": true, "ast": { "tipo": "PROGRAMA", ... }, "erros": [] }
}
```

O bloco `sintatico` varia conforme o caso:

1. análise léxica e sintática sem erros: `executado` e `sucesso` em `true`, e `ast` com a árvore (formato em `docs/ast.md`);
2. erro sintático: `executado` em `true`, `sucesso` em `false`, `ast` em `null` e a lista `erros` com um objeto por erro, cada um com `linha`, `coluna`, `encontrado`, `esperado`, `regra` e `mensagem`;
3. erro léxico: `executado` em `false`, `sucesso` em `false`, `ast` em `null`, `erros` vazio e um campo `motivo` explicando que o parser não foi executado.

A mensagem muda de acordo: "Análise léxica e sintática concluídas sem erros: N token(s) e M nó(s) na AST.", ou "Análise léxica sem erros; análise sintática com K erro(s).", ou a mensagem léxica seguida de "A análise sintática não foi executada.". O HTTP é 200 nos três casos; a troca de mensagem é uma alteração intencional de contrato, registrada em `docs/testes.md`. Entradas inválidas continuam 400, sem os blocos.

### Explicação com IA

O endpoint `POST /api/ia/explicar` recebe `{ "tipo", "codigo", "alvo", "pergunta" }`, onde `tipo` é `TOKEN`, `NO_AST`, `ERRO_SINTATICO`, `ERRO_LEXICO` ou `PERGUNTA`. O backend reexecuta o scanner e o parser sobre o código e monta o contexto a partir desse resultado, sem confiar em tokens ou AST enviados pelo navegador. A resposta 200 é `{ "explicacao", "modelo", "geradoPorIA" }`; os códigos 400, 502, 503 e 504 indicam, respectivamente, entrada inválida, resposta inválida do Ollama, Ollama indisponível e tempo esgotado, sempre sem expor endereço ou porta. Os detalhes estão na seção "Explicações com IA (Ollama)".

Erros léxicos mantêm o código HTTP 200. Adotou-se essa decisão porque a requisição foi recebida e processada corretamente; o erro pertence ao programa analisado, e não à comunicação. Assim, o resultado da análise é informado pelos campos `sucesso` e `erros`, e os códigos 4xx e 5xx ficam reservados a falhas da requisição ou do servidor.

Resposta em caso de entrada inválida (HTTP 400), sem o campo `tokens`, inalterada em relação à etapa 2:

```json
{ "recebido": false, "erro": "Informe um código-fonte antes de solicitar a análise." }
```

Outros códigos retornados: 404 para rota inexistente, 405 para método não permitido e 500 para erro inesperado (inclusive uma eventual exceção no scanner), sempre com uma mensagem genérica que não expõe detalhes internos do servidor.

## Interface

A tela é organizada em duas colunas no computador (acima de 900 pixels): à esquerda, fixa ao rolar, ficam o seletor de exemplos, o editor de código e o botão Analisar; à direita, os resultados. Os resultados são divididos em abas, para não empilhar tudo em uma coluna longa: Tokens (resumo, código destacado, passo a passo do scanner e tabela), Árvore (AST) (a árvore, os detalhes do nó, a construção passo a passo, o filtro e a exportação), Erros (léxicos e sintáticos separados, com um contador no nome da aba) e Professor IA. As abas usam `role="tablist"` e `role="tab"`, trocam por clique e pelas setas do teclado, e os textos explicativos ficam recolhidos em `details` dentro de cada aba. Depois de analisar, abre automaticamente a aba Erros quando há erro e a aba Árvore (AST) quando não há; ao pedir uma explicação com IA, a aba Professor IA é aberta. No celular (até 600 pixels) fica uma coluna só, com o editor em cima e as abas abaixo, que rolam na horizontal quando não cabem.

A tela principal contém:

1. Identificação do sistema e da linguagem analisada, com a indicação "Fases disponíveis: análise léxica (scanner) e análise sintática (parser e AST)";
2. Um painel expansível "Como usar e o que é análise léxica", com a explicação dos conceitos de token e lexema e os passos de uso;
3. Seletor de exemplos de programas;
4. Área de entrada de código com fonte monoespaçada, na qual é possível escrever, colar e editar o programa;
5. Botão "Analisar", que envia o código ao backend;
6. Área de resultados, que exibe a mensagem da análise e as mensagens de validação e de erro;
7. Seção "Análise léxica", exibida somente após uma análise válida, composta por:
   1. Resumo com a quantidade de tokens de cada categoria, o total de tokens e o total de erros léxicos;
   2. Código destacado, no qual cada token recebe a cor da sua categoria e cada erro léxico é sublinhado em vermelho, enquanto espaços e comentários aparecem como texto simples;
   3. Passo a passo do autômato, com os botões "Anterior", "Reproduzir" (que alterna para "Pausar") e "Próximo", a escolha da velocidade (lenta, normal ou rápida) e as setas esquerda e direita do teclado. Para o token atual, são exibidos sua posição, a categoria com uma breve explicação e as transições percorridas, no formato `inicial --'1'--> inteiro`. O token atual é destacado no código e na tabela;
   4. Tabela de tokens com número, categoria, lexema, linha e coluna; ao clicar em uma linha (ou pressionar Enter sobre ela), o token correspondente é selecionado no passo a passo;
   5. Lista de erros léxicos, com uma mensagem por erro, ou a indicação "Nenhum erro léxico encontrado.".
8. Seção "Análise sintática e AST", exibida após a primeira análise, composta por:
   1. Painéis expansíveis com a explicação da fase (parser, gramática, AST e a diferença entre tokens, árvore de derivação e AST) e com a gramática do MiniC para consulta;
   2. Quando o parser não é executado por erro léxico, o motivo; quando há erros sintáticos, a lista de erros, cada um com rótulo "Erro sintático", a mensagem, o esperado, o encontrado e a regra violada. Os erros léxicos continuam na lista da etapa 3, com a diferença visível por texto, e não apenas por cor;
   3. A AST como árvore navegável (`role="tree"`), em que cada nó mostra o rótulo (tipo e valor ou nome) e uma marca de categoria em texto (Declaração, Comando, Operação, Valor). A navegação por teclado usa as setas para cima e para baixo entre os nós, a direita para expandir, a esquerda para recolher e Enter para selecionar;
   4. Ao selecionar um nó, o trecho correspondente é destacado no código e na tabela de tokens, e um painel mostra o tipo, a regra, o papel, a posição e os atributos do nó;
   5. Botões para expandir e recolher tudo, um filtro por tipo de nó, a exportação da AST em JSON e a construção passo a passo (os mesmos controles de velocidade e reprodução do passo a passo do scanner), que mostra os nós na ordem em que o parser os criou;
9. Botões "Explicar com IA" no painel do nó, em cada erro e no passo a passo do scanner, além da área "Professor virtual" com sugestões de perguntas; a resposta aparece em um painel próprio, com o aviso de que foi gerada por IA e pode conter erros.

Ao selecionar um exemplo, seu código substitui o conteúdo da área de entrada e a análise anterior é ocultada. Se o código for editado depois de uma análise, a interface avisa que o resultado exibido está desatualizado e marca as seções léxica e sintática como desatualizadas. A seção de análise também é ocultada quando a entrada é vazia, quando há falha de comunicação ou quando o servidor responde fora do contrato esperado.

Quanto à acessibilidade e ao uso em celular, a categoria de cada token é sempre indicada por texto (na tabela, no resumo e no passo a passo), e não apenas pela cor; os elementos interativos apresentam foco visível; os botões têm altura mínima de 44 pixels; e, em telas de até 600 pixels de largura, os botões de controle ocupam toda a largura e a tabela pode ser rolada horizontalmente. Todo o conteúdo proveniente do código do usuário é inserido como texto (`textContent`), e não como HTML, o que impede a interpretação de marcações digitadas no código.

## Exemplos disponíveis

| Exemplo | Construções demonstradas |
|---|---|
| Exemplo 1: Declaração e inicialização de variáveis | Palavras reservadas `int` e `float`, identificadores, literal inteiro e literal real |
| Exemplo 2: Operações aritméticas | Operadores `+`, `-`, `*`, `/` e `=`, delimitadores `(` e `)` |
| Exemplo 3: Estrutura condicional | Palavras reservadas `if` e `else`, operador `>`, delimitadores `{` e `}` |
| Exemplo 4: Comentários e operadores relacionais | Comentário de linha, comentário de bloco com mais de uma linha e operadores `!=` e `<=` |
| Exemplo 5: Código com erros léxicos | Literal malformado `7.5.1`, caractere não reconhecido `@` e comentário de bloco sem fechamento |
| Exemplo 6: Precedência e associatividade (AST) | A multiplicação abaixo da adição, a subtração associativa à esquerda e os parênteses mudando a árvore |
| Exemplo 7: if, else if e else com blocos aninhados | Condicional encadeada, blocos com declarações e comandos aninhados |
| Exemplo 8: Código com erros sintáticos | Dois erros sintáticos em linhas diferentes, sem erros léxicos, para mostrar a recuperação |

## Validações e mensagens de erro

| Situação | Onde é tratada | Mensagem exibida |
|---|---|---|
| Entrada vazia | Frontend e backend | Informe um código-fonte antes de solicitar a análise. |
| Entrada apenas com espaços | Frontend e backend | O código informado contém apenas espaços em branco. Escreva um programa antes de solicitar a análise. |
| Campo ausente, tipo inválido ou corpo que não é JSON | Backend | Requisição inválida, com a descrição do problema |
| Código acima de 10000 caracteres | Backend | O código excede o limite de 10000 caracteres. |
| Erro léxico | Backend (scanner) e frontend | Mensagem com linha, coluna, lexema e orientação, conforme a seção "Escopo léxico" |
| Código alterado após a análise | Frontend | O código foi alterado depois da última análise. Clique em Analisar para atualizar os tokens. |
| Falha de comunicação com o servidor | Frontend | Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente. |
| Resposta fora do contrato ou erro inesperado | Frontend e backend | Mensagem genérica, sem detalhes internos |

Código com erros de sintaxe, mas formado apenas por tokens válidos, é analisado sem erros léxicos, uma vez que a detecção de erros sintáticos será implementada na etapa 4.

## Explicações com IA (Ollama)

O Ollama é um programa que executa modelos de linguagem localmente, sem depender de serviços externos. Aqui ele serve apenas para explicar os resultados da análise de forma didática: tokens, AST e erros continuam sendo produzidos pelo scanner e pelo parser, e a análise funciona normalmente com o Ollama desligado.

O modelo usado é o Llama 3.2 na versão de 3 bilhões de parâmetros (`llama3.2`), escolhido por caber em uma máquina comum (cerca de 4 GB de RAM livres).

No `docker-compose.yml`, o Ollama entrou como um serviço próprio, com um volume `ollama_data` para guardar o modelo baixado. A porta 11434 não é publicada no host: só o backend fala com o Ollama, pela rede interna do Docker. O backend recebeu as variáveis `OLLAMA_BASE_URL` (padrão `http://ollama:11434`), `OLLAMA_MODEL` (padrão `llama3.2`) e `OLLAMA_TIMEOUT` (padrão 120 segundos). O healthcheck do backend não depende do Ollama, para que o frontend não fique esperando o modelo. No `nginx.conf`, o caminho `/api/ia/` tem um tempo de leitura maior (150 segundos), pois o modelo pode demorar mais que os 60 segundos padrão do Nginx quando roda na CPU.

Para baixar o modelo, com os contêineres em execução:

```bash
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama list
```

O backend fala com o Ollama em `backend/ia.py`, usando apenas `urllib`. Antes de cada explicação, ele consulta `GET /api/tags` para saber se o modelo está instalado; depois, envia o contexto por `POST /api/chat`, com `temperature` 0.2 e sem streaming. A chamada é repetida no máximo uma vez, e só em falha de conexão; em tempo esgotado, não há nova tentativa. O contexto é montado reexecutando o scanner e o parser sobre o código recebido, de modo que o modelo recebe só dados produzidos pelo compilador. O código, os tokens e a AST vão entre os marcadores `<dados>` e `</dados>`, e uma instrução de sistema orienta o modelo a não inventar e a ignorar instruções que apareçam dentro dos dados.

Na interface, há botões "Explicar com IA" no painel do nó selecionado, em cada erro sintático, em cada erro léxico e no passo a passo do scanner, além da área "Professor virtual", com sugestões de perguntas. A resposta aparece em um painel com aviso fixo de que foi gerada por IA e pode conter erros, e com mensagens claras quando o assistente está indisponível, demora demais ou responde de forma inválida. O texto é exibido com `textContent` (sem interpretar HTML); como o modelo costuma responder em Markdown, os marcadores de formatação (`**`, crases, títulos e marcadores de lista) são removidos antes de exibir, para não aparecerem crus. A interface nunca fala com o Ollama direto: só chama `/api/ia/explicar`.

Os testes da IA usam a chamada HTTP substituída por um dublê (sem Ollama real):

```bash
docker compose run --rm backend pytest -v tests/test_ia.py
```

O teste de integração real é pulado por padrão e só roda com a variável `OLLAMA_INTEGRACAO=1`:

```bash
docker compose exec -e OLLAMA_INTEGRACAO=1 backend pytest -v tests/test_ia.py
```

O script `tests/ia.sh` verifica, com os contêineres em execução, se o contêiner do Ollama está rodando, se o `llama3.2` aparece em `ollama list` e se `POST /api/ia/explicar` responde com uma explicação não vazia. Em uma execução com o modelo instalado (2.0 GB), o `tests/ia.sh` passou nas 4 verificações e o `pytest -v tests/test_ia.py` com `OLLAMA_INTEGRACAO=1` passou nos 19 testes, incluindo a integração real. A persistência foi confirmada: após `docker compose down` (sem `-v`) e `up`, o `ollama list` continuou mostrando o `llama3.2` sem novo download.

### Exemplo da demonstração

Requisição a `POST /api/ia/explicar` (pelo proxy em `http://localhost:8080`):

```json
{ "tipo": "NO_AST", "codigo": "int resultado = 10 + 5 * 2;", "alvo": 4,
  "pergunta": "Por que a multiplicação aparece abaixo da adição?" }
```

O backend reexecutou o scanner e o parser, montou o contexto do nó de id 4 (a MULTIPLICACAO) com o nó pai, os filhos e a gramática, e enviou ao modelo. A resposta (HTTP 200, `geradoPorIA` true, modelo `llama3.2`) levou cerca de 25,6 segundos na CPU e começou assim:

"Vamos analisar a estrutura da AST: o nó pai é a ADICAO, com papel valor. O trecho é '10 + 5 * 2'... A multiplicativa é um nó filho direto da ADICAO, com papel direita e atributos (operador=*) e trecho '5 * 2'... A razão pela qual a multiplicação aparece abaixo da adição é que a gramática do MiniC define a expressão aditiva como composta por termos multiplicativos..."

Limitações: a resposta pode demorar na CPU (no exemplo acima, cerca de 25 segundos); o modelo pode errar, por isso o resultado oficial é sempre o do compilador (a explicação do exemplo mistura um pouco os conceitos); e o modelo precisa de memória suficiente para ser carregado (cerca de 4 GB livres para o modelo de 3B).

## Pré-requisitos

1. Git;
2. Docker 24 ou superior;
3. Docker Compose v2 (comando `docker compose`);
4. curl, utilizado pelo teste de implantação.

Para executar os testes fora dos contêineres, também são necessários Python 3.12 e Node.js 18 ou superior.

## Como executar

```bash
git clone https://github.com/Anavalerianob/compiladores-minic.git
cd compiladores-minic
docker compose up --build -d
```

Em seguida, acessar `http://localhost:8080` no navegador.

## Como encerrar

```bash
docker compose down
```

Para remover também as imagens construídas:

```bash
docker compose down --rmi local
```

O modelo baixado fica no volume `ollama_data` e sobrevive a um `docker compose down` comum. Para não precisar baixar o modelo de novo, evite as opções `-v` (que apaga os volumes) e `--rmi all` (que apaga também a imagem do Ollama).

## Testes

Testes do backend (scanner, validação e endpoints) com pytest:

```bash
docker compose run --rm backend pytest -v
```

Esse comando cobre o scanner, o parser, a API e a IA (com mock). Para rodar um conjunto específico, basta indicar o arquivo, por exemplo `tests/test_parser.py` ou `tests/test_ia.py`.

Fora do contêiner, os mesmos comandos podem ser executados a partir da pasta `backend`, com `pytest -v` e `pytest -v tests/test_parser.py`.

Testes de interface do frontend (node:test e jsdom):

```bash
cd frontend
npm install
npm test
```

Teste de implantação, com os contêineres em execução:

```bash
sh tests/implantacao.sh
```

O teste de implantação verifica se a interface está acessível, se o backend responde por meio do proxy, se um código válido é aceito, se um código vazio é rejeitado, se a resposta para `int numero = 10;` contém o token de lexema `numero`, se a resposta para `int a = 5 @ 2;` indica `"sucesso":false`, se a análise de `int resultado = 10 + 5 * 2;` contém `MULTIPLICACAO` e se a análise de `int x = 5` contém `ERRO_SINTATICO`.

O teste da IA, manual, roda com `sh tests/ia.sh`, com os contêineres em execução e o modelo baixado.

### Resultados

| Conjunto | Aprovados | Reprovados |
|---|---|---|
| Backend: scanner (regressão) | 77 | 0 |
| Backend: parser e AST | 47 | 0 |
| Backend: validação, endpoints e contrato da etapa 4 | 30 | 0 |
| Backend: IA com mock (integração real pulada) | 18 | 0 |
| Frontend: interface, AST e IA (comunicação simulada) | 71 | 0 |

A execução do backend resultou em 172 testes aprovados e 1 pulado por padrão, e a do frontend, em 79 aprovados. Com o modelo `llama3.2` instalado, a integração real do Ollama também foi executada (`OLLAMA_INTEGRACAO=1`), com 19 testes de IA aprovados, e o `tests/ia.sh` passou nas 4 verificações. A construção das imagens do zero, a subida dos contêineres e o teste de implantação (9 verificações) foram validados. O `docs/testes.md` traz o registro detalhado, as falhas encontradas, as correções, as alterações intencionais de contrato e a demonstração da IA.

## Validação de instalação limpa

```bash
docker compose down --rmi local
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama list
sh tests/implantacao.sh
sh tests/ia.sh
docker compose run --rm backend pytest -v
docker compose exec -e OLLAMA_INTEGRACAO=1 backend pytest -v tests/test_ia.py
cd frontend && npm install && npm test
```

As opções `--rmi all` e `-v` são evitadas de propósito, para não apagar o modelo baixado. Em seguida, acessar `http://localhost:8080`, digitar `int resultado = 10 + 5 * 2;`, ver os tokens e a AST, selecionar o nó de multiplicação, pedir a explicação com IA e, depois, analisar um código com erro sintático e pedir a explicação do erro.

## Limitações conhecidas

1. O sistema não realiza análise semântica (tabela de símbolos, tipos, variável não declarada); essa fase será implementada na etapa 5. O parser só verifica a estrutura e constrói a AST, então um programa como `x = y + 1;` com `y` não declarado é aceito.
2. A interface exibe a AST e não exibe a árvore de derivação, que mostraria cada regra aplicada e todos os terminais, inclusive `;` e os parênteses.
3. A gramática não inclui laços, funções, `return`, operadores lógicos, strings, vetores nem ponteiros; essas construções estão fora do subconjunto, e o `if` exige bloco com chaves.
4. O escopo léxico não inclui strings, caracteres literais, operadores lógicos (`&&`, `||`, `!`), laços (`while`, `for`), `return`, funções nem diretivas de pré-processador (`#include`); esses elementos são informados como erros léxicos ou reconhecidos como identificadores.
5. Os identificadores aceitam somente caracteres ASCII; letras acentuadas são informadas como erros léxicos.
6. O passo a passo apresenta as transições do autômato em forma textual, sem desenho gráfico do autômato.
7. Os testes de interface simulam o servidor e não substituem testes de ponta a ponta automatizados em navegador real.
8. A área de entrada não possui realce de sintaxe durante a digitação nem numeração de linhas; o destaque por categoria aparece somente após a análise.
9. A explicação com IA é opcional e local: pode demorar na CPU e pode conter erros, por isso o resultado oficial é sempre o do compilador.
