# MiniC Analisador

Disciplina: ICE0619 Compiladores (UFJ, 2026.2)
Autora: Ana Luísa Valeriano Bomfim

## Objetivo

O MiniC Analisador é um software educacional cujo propósito é realizar a análise léxica, sintática e semântica de programas escritos em um subconjunto da linguagem C, exibindo os resultados em uma interface web, de modo a auxiliar estudantes na compreensão do processo de compilação.

Na versão atual (etapa 2), o sistema permite escrever, colar ou selecionar um programa, enviá-lo ao backend e visualizar a resposta. As análises léxica, sintática e semântica ainda não foram implementadas e serão desenvolvidas nas próximas etapas.

## Linguagem escolhida e subconjunto previsto

Optou-se pela linguagem C, haja vista que se trata da linguagem utilizada nas disciplinas introdutórias de programação do curso, de modo que seu público-alvo já possui familiaridade com sua sintaxe. Ademais, sua gramática é relativamente regular e amplamente documentada na literatura de compiladores.

O subconjunto previsto (MiniC) abrange:

1. Declaração de variáveis dos tipos `int` e `float`, com inicialização opcional;
2. Atribuição de valores a variáveis;
3. Operadores aritméticos `+`, `-`, `*` e `/`, com uso de parênteses;
4. Operadores relacionais `==`, `!=`, `<`, `<=`, `>` e `>=`;
5. Estrutura condicional `if`/`else`.

Laços de repetição, funções, vetores, ponteiros e structs foram deliberadamente excluídos, porquanto abranger a linguagem inteira de uma só vez tornaria o projeto inviável.

## Tecnologias utilizadas

1. Frontend: HTML, CSS e JavaScript puro, servidos pelo Nginx;
2. Backend: Python 3.12 com Flask;
3. Testes: pytest (backend), node:test com jsdom (frontend) e script shell com curl (implantação);
4. Ambiente: Docker e Docker Compose.

## Estrutura do repositório

```
.
├── backend/
│   ├── app.py               Rotas da API e tratamento de erros
│   ├── validacao.py         Validações da entrada recebida
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/test_api.py    Testes unitários e dos endpoints
├── frontend/
│   ├── index.html           Tela principal
│   ├── app.js               Exemplos, validação e comunicação com o backend
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

{ "codigo": "int numero = 10;" }
```

Resposta em caso de sucesso (HTTP 200):

```json
{ "recebido": true, "mensagem": "Código recebido com sucesso.", "linhas": 1, "caracteres": 16 }
```

Resposta em caso de entrada inválida (HTTP 400):

```json
{ "recebido": false, "erro": "Informe um código-fonte antes de solicitar a análise." }
```

Outros códigos retornados: 404 para rota inexistente, 405 para método não permitido e 500 para erro inesperado, sempre com uma mensagem genérica que não expõe detalhes internos do servidor.

## Interface

A tela principal contém:

1. Identificação do sistema e da linguagem analisada;
2. Seletor de exemplos de programas;
3. Área de entrada de código com fonte monoespaçada, na qual é possível escrever, colar e editar o programa;
4. Botão "Analisar", que envia o código ao backend;
5. Área de resultados, que exibe mensagens de sucesso, de validação e de erro.

Ao selecionar um exemplo, seu código substitui o conteúdo da área de entrada e pode ser editado antes do envio. O código digitado permanece no campo após a análise.

## Exemplos disponíveis

| Exemplo | Construções demonstradas |
|---|---|
| Exemplo 1: Declaração e inicialização de variáveis | Declaração de `int` e `float`, com e sem inicialização |
| Exemplo 2: Operações aritméticas | Operadores `+`, `-`, `*`, `/` e uso de parênteses |
| Exemplo 3: Estrutura condicional | `if`/`else`, operador relacional `>` e atribuição |
| Exemplo 4: Código com erro intencional | Expressão incompleta e ausência de ponto e vírgula, para demonstrar a detecção de erros nas próximas etapas |

## Validações e mensagens de erro

| Situação | Onde é tratada | Mensagem exibida |
|---|---|---|
| Entrada vazia | Frontend e backend | Informe um código-fonte antes de solicitar a análise. |
| Entrada apenas com espaços | Frontend e backend | O código informado contém apenas espaços em branco. Escreva um programa antes de solicitar a análise. |
| Campo ausente, tipo inválido ou corpo que não é JSON | Backend | Requisição inválida, com a descrição do problema |
| Código acima de 10000 caracteres | Backend | O código excede o limite de 10000 caracteres. |
| Falha de comunicação com o servidor | Frontend | Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente. |
| Erro inesperado | Frontend e backend | Mensagem genérica, sem detalhes internos |

Código com erros de sintaxe é aceito normalmente, uma vez que será utilizado nas próximas etapas para demonstrar a detecção de erros.

## Pré-requisitos

1. Git;
2. Docker 24 ou superior;
3. Docker Compose v2 (comando `docker compose`).

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

Testes unitários e dos endpoints do backend (pytest):

```bash
docker compose run --rm backend pytest -v
```

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

O teste de implantação verifica se a interface está acessível, se o backend responde por meio do proxy, se um código válido é aceito e se um código vazio é rejeitado.

### Resultados

| Conjunto | Aprovados | Reprovados |
|---|---|---|
| Backend (unitários, endpoints e regressão) | 21 | 0 |
| Frontend (interface e comunicação simulada) | 19 | 0 |
| Implantação | 5 | 0 |

O registro detalhado, incluindo falhas encontradas e correções realizadas, encontra-se em `docs/testes.md`.

## Validação de instalação limpa

```bash
docker compose down --rmi all
docker compose build --no-cache
docker compose up -d
sh tests/implantacao.sh
```

Em seguida, acessar `http://localhost:8080`, selecionar um exemplo, editá-lo e clicar em "Analisar", verificando se a mensagem de sucesso é exibida.

## Limitações conhecidas

1. O sistema ainda não realiza análise léxica, sintática ou semântica; o backend apenas recebe e valida o código.
2. Os testes de interface simulam o servidor e não substituem testes de ponta a ponta automatizados em navegador real.
3. A área de entrada não possui realce de sintaxe nem numeração de linhas.
