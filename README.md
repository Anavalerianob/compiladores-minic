# MiniC Analisador

Disciplina: ICE0619 Compiladores (UFJ, 2026.2)
Autora: Ana Luísa Valeriano Bomfim

## Objetivo

O MiniC Analisador é um software educacional cujo propósito é realizar a análise léxica, sintática e semântica de programas escritos em um subconjunto da linguagem C, exibindo os resultados em uma interface web, de modo a auxiliar estudantes na compreensão do processo de compilação.

Na versão atual (etapa 3), o analisador léxico (scanner) está implementado e integrado à aplicação. O sistema permite escrever, colar ou selecionar um programa, enviá-lo ao backend e visualizar os tokens reconhecidos, os erros léxicos com linha e coluna e a execução passo a passo do autômato que reconheceu cada token. As análises sintática e semântica ainda não foram implementadas e serão desenvolvidas nas etapas 4 e 5.

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

## Tecnologias utilizadas

1. Frontend: HTML, CSS e JavaScript puro, servidos pelo Nginx;
2. Backend: Python 3.12 com Flask;
3. Testes: pytest (backend), node:test com jsdom (frontend) e script shell com curl (implantação);
4. Ambiente: Docker e Docker Compose.

Nenhuma dependência nova foi acrescentada na etapa 3.

## Estrutura do repositório

```
.
├── backend/
│   ├── app.py               Rotas da API e tratamento de erros
│   ├── scanner.py           Analisador léxico (scanner)
│   ├── validacao.py         Validações da entrada recebida
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│       ├── test_api.py      Testes unitários da validação e dos endpoints
│       └── test_scanner.py  Testes unitários do scanner
├── frontend/
│   ├── index.html           Tela principal
│   ├── app.js               Exemplos, validação, comunicação e exibição da análise léxica
│   ├── nginx.conf           Servidor web e proxy para o backend
│   ├── package.json         Dependências e comando dos testes
│   ├── Dockerfile
│   └── tests/interface.test.js   Testes de interface
├── tests/implantacao.sh     Teste de implantação
├── docs/testes.md           Registro dos testes executados
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

Após validar a entrada, o backend executa o scanner e responde com HTTP 200. A resposta abaixo foi obtida executando a API com a requisição acima (as chaves são ordenadas alfabeticamente pelo Flask):

```json
{
  "caracteres": 14,
  "erros": [],
  "linhas": 1,
  "mensagem": "Análise léxica concluída sem erros: 5 token(s) reconhecido(s).",
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

Quando há erros léxicos, o campo `sucesso` vale `false`, a lista `erros` contém um objeto por erro e a mensagem passa a ser, por exemplo, `Análise léxica concluída com 1 erro(s) léxico(s) e 6 token(s) reconhecido(s).` (resposta para `int a = 5 @ 2;`).

Erros léxicos mantêm o código HTTP 200. Adotou-se essa decisão porque a requisição foi recebida e processada corretamente; o erro pertence ao programa analisado, e não à comunicação. Assim, o resultado da análise é informado pelos campos `sucesso` e `erros`, e os códigos 4xx e 5xx ficam reservados a falhas da requisição ou do servidor.

Resposta em caso de entrada inválida (HTTP 400), sem o campo `tokens`, inalterada em relação à etapa 2:

```json
{ "recebido": false, "erro": "Informe um código-fonte antes de solicitar a análise." }
```

Outros códigos retornados: 404 para rota inexistente, 405 para método não permitido e 500 para erro inesperado (inclusive uma eventual exceção no scanner), sempre com uma mensagem genérica que não expõe detalhes internos do servidor.

## Interface

A tela principal contém:

1. Identificação do sistema e da linguagem analisada, com a indicação "Fase disponível: análise léxica (scanner)";
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

Ao selecionar um exemplo, seu código substitui o conteúdo da área de entrada e a análise anterior é ocultada. Se o código for editado depois de uma análise, a interface avisa que o resultado exibido está desatualizado. A seção de análise também é ocultada quando a entrada é vazia, quando há falha de comunicação ou quando o servidor responde fora do contrato esperado.

Quanto à acessibilidade e ao uso em celular, a categoria de cada token é sempre indicada por texto (na tabela, no resumo e no passo a passo), e não apenas pela cor; os elementos interativos apresentam foco visível; os botões têm altura mínima de 44 pixels; e, em telas de até 600 pixels de largura, os botões de controle ocupam toda a largura e a tabela pode ser rolada horizontalmente. Todo o conteúdo proveniente do código do usuário é inserido como texto (`textContent`), e não como HTML, o que impede a interpretação de marcações digitadas no código.

## Exemplos disponíveis

| Exemplo | Construções demonstradas |
|---|---|
| Exemplo 1: Declaração e inicialização de variáveis | Palavras reservadas `int` e `float`, identificadores, literal inteiro e literal real |
| Exemplo 2: Operações aritméticas | Operadores `+`, `-`, `*`, `/` e `=`, delimitadores `(` e `)` |
| Exemplo 3: Estrutura condicional | Palavras reservadas `if` e `else`, operador `>`, delimitadores `{` e `}` |
| Exemplo 4: Comentários e operadores relacionais | Comentário de linha, comentário de bloco com mais de uma linha e operadores `!=` e `<=` |
| Exemplo 5: Código com erros léxicos | Literal malformado `7.5.1`, caractere não reconhecido `@` e comentário de bloco sem fechamento |

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
docker compose down --rmi all
```

## Testes

Testes do backend (scanner, validação e endpoints) com pytest:

```bash
docker compose run --rm backend pytest -v
```

Somente os testes unitários do scanner:

```bash
docker compose run --rm backend pytest -v tests/test_scanner.py
```

Fora do contêiner, os mesmos comandos podem ser executados a partir da pasta `backend`, com `pytest -v` e `pytest -v tests/test_scanner.py`.

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

O teste de implantação verifica se a interface está acessível, se o backend responde por meio do proxy, se um código válido é aceito, se um código vazio é rejeitado, se a resposta para `int numero = 10;` contém o token de lexema `numero` e se a resposta para `int a = 5 @ 2;` indica `"sucesso":false`.

### Resultados

| Conjunto | Aprovados | Reprovados |
|---|---|---|
| Backend: scanner (unitários) | 77 | 0 |
| Backend: validação, endpoints e regressão | 26 | 0 |
| Frontend: interface e comunicação simulada | 42 | 0 |
| Implantação | 7 | 0 |

Os testes do backend foram executados no contêiner (Python 3.12) após a construção das imagens do zero, e os do frontend, com Node.js 22. O registro detalhado, incluindo a validação em instalação limpa, as falhas encontradas, as correções e as alterações intencionais de comportamento, encontra-se em `docs/testes.md`.

## Validação de instalação limpa

```bash
docker compose down --rmi all
docker compose build --no-cache
docker compose up -d
docker compose ps
sh tests/implantacao.sh
docker compose run --rm backend pytest -v
```

Em seguida, acessar `http://localhost:8080`, selecionar o Exemplo 5, clicar em "Analisar" e verificar a tabela de tokens, o código destacado, a lista de erros e o passo a passo.

## Limitações conhecidas

1. O sistema não realiza análise sintática nem semântica; essas fases serão implementadas nas etapas 4 e 5.
2. O escopo léxico não inclui strings, caracteres literais, operadores lógicos (`&&`, `||`, `!`), laços (`while`, `for`), `return`, funções nem diretivas de pré-processador (`#include`); esses elementos são informados como erros léxicos ou reconhecidos como identificadores.
3. Os identificadores aceitam somente caracteres ASCII; letras acentuadas são informadas como erros léxicos.
4. O passo a passo apresenta as transições do autômato em forma textual, sem desenho gráfico do autômato.
5. Os testes de interface simulam o servidor e não substituem testes de ponta a ponta automatizados em navegador real.
6. A área de entrada não possui realce de sintaxe durante a digitação nem numeração de linhas; o destaque por categoria aparece somente após a análise.
