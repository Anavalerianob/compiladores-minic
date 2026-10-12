# Trabalho 1 - Compiladores

Disciplina: ICE0619 Compiladores (UFJ, 2026.2)
Autora: Ana Luísa Valeriano Bomfim

## Sobre o projeto

Este repositório contém a primeira etapa de um software educacional cujo objetivo é realizar a análise léxica, sintática e semântica de programas escritos em um subconjunto da linguagem C, exibindo os resultados em uma interface web. Nesta fase, foi construída apenas a base do projeto: uma aplicação web mínima, composta por frontend e backend, executada em contêineres Docker e orquestrada pelo Docker Compose. As funcionalidades de análise serão implementadas nas etapas seguintes.

## Linguagem escolhida

Optou-se pela linguagem C, haja vista que se trata da linguagem utilizada nas disciplinas introdutórias de programação do curso, de modo que seu público-alvo já possui familiaridade com sua sintaxe. Ademais, sua gramática é relativamente regular e amplamente documentada na literatura de compiladores, o que favorece a construção incremental dos analisadores.

## Subconjunto inicial

Nesta primeira versão, serão tratadas apenas as seguintes construções:

1. Declaração de variáveis dos tipos `int` e `float`;
2. Atribuição de valores a variáveis;
3. Operadores aritméticos `+`, `-`, `*` e `/`, com uso de parênteses;
4. Estrutura condicional `if`/`else`.

Exemplo de programa aceito pelo subconjunto:

```c
int a;
float b;
a = 10;
b = (a + 2) * 3.5;
if (a > 5) {
    b = b - 1;
} else {
    b = 0;
}
```

Construções como laços de repetição, funções, vetores, ponteiros e structs foram deliberadamente excluídas neste momento, porquanto tentar abranger a linguagem inteira de uma só vez tornaria o projeto inviável. Por conseguinte, tais elementos poderão ser incorporados gradualmente nas próximas etapas, sem necessidade de reestruturar a base.

## Estrutura do repositório

```
.
├── backend/
│   ├── app.py              API em Python (Flask) que responde "Hello, World!"
│   ├── requirements.txt    Dependências do backend
│   └── Dockerfile          Instruções para construir o contêiner do backend
├── frontend/
│   ├── index.html          Página web que consulta o backend e exibe a mensagem
│   └── Dockerfile          Instruções para construir o contêiner do frontend (Nginx)
├── docker-compose.yml      Orquestração dos dois serviços
└── README.md
```

## Arquitetura

O projeto é composto por dois serviços:

1. Backend: aplicação Flask executada na porta 5000, que expõe a rota `/hello` e retorna a mensagem "Hello, World!" em formato JSON. É nele que os analisadores léxico, sintático e semântico serão implementados futuramente.
2. Frontend: página HTML servida pelo Nginx na porta 8080, responsável por exibir a interface ao usuário. Ao ser carregada, a página faz uma requisição ao backend e mostra a mensagem recebida.

Não foi incluído banco de dados, uma vez que o projeto ainda não o exige nesta etapa.

## Pré-requisitos

Para executar o projeto, é necessário ter instalado:

1. Git;
2. Docker 24 ou superior;
3. Docker Compose v2 (acessível pelo comando `docker compose`).

As versões instaladas podem ser verificadas com:

```bash
docker --version
docker compose version
```

## Como executar

1. Clonar o repositório e acessar a pasta do projeto:

```bash
git clone https://github.com/Anavalerianob/compiladores-trabalho1.git
cd compiladores-trabalho1
```

2. Construir as imagens e subir os contêineres:

```bash
docker compose up --build -d
```

3. Acessar `http://localhost:8080` no navegador.

Se tudo estiver correto, a página exibirá a mensagem "Hello, World!". Como essa mensagem é fornecida pelo backend, sua exibição comprova que o frontend está no ar, que o backend está respondendo e que a comunicação entre ambos ocorre sem erros.

Também é possível testar o backend diretamente:

```bash
curl http://localhost:5000/hello
```

## Como encerrar

Para parar e remover os contêineres:

```bash
docker compose down
```

Para remover também as imagens construídas:

```bash
docker compose down --rmi all
```

## Validação de instalação limpa

Com o intuito de garantir que o projeto não dependa de nenhuma configuração existente apenas na máquina de desenvolvimento, deve-se simular o ambiente de uma pessoa que nunca teve contato com ele:

```bash
docker compose down --rmi all
docker compose build --no-cache
docker compose up -d
```

Em seguida, acessar `http://localhost:8080` e verificar se a mensagem "Hello, World!" é exibida. Caso algum passo falhe, a documentação ou a configuração deve ser corrigida até que o processo seja totalmente reproduzível.
