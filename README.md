# MiniC Analisador

Software educacional desenvolvido para a disciplina ICE0619 Compiladores (UFJ, 2026.2), cujo propósito é realizar a análise léxica, sintática e semântica de programas escritos em um subconjunto da linguagem C, exibindo os resultados de cada etapa em uma interface web, de modo a auxiliar estudantes iniciantes na compreensão do processo de compilação.

Autora: Ana Luísa Valeriano Bomfim

## Linguagem escolhida

Optou-se pela linguagem C, haja vista que se trata da linguagem utilizada nas disciplinas introdutórias de programação do curso, de sorte que os estudantes já possuem familiaridade com sua sintaxe. Ademais, sua gramática é relativamente regular e amplamente documentada na literatura de compiladores, o que favorece a implementação incremental dos analisadores.

## Subconjunto inicial (MiniC)

Nesta primeira versão, serão tratadas apenas as seguintes construções:

1. Declaração de variáveis dos tipos `int` e `float`, com inicialização opcional;
2. Atribuição;
3. Operadores aritméticos `+`, `-`, `*` e `/`, com uso de parênteses;
4. Operadores relacionais `==`, `!=`, `<`, `<=`, `>` e `>=`;
5. Estrutura condicional `if` e `if`/`else`, com blocos delimitados por chaves.

Ficam excluídos, por ora, ponteiros, vetores, structs, laços de repetição, funções definidas pelo usuário e diretivas de pré-processador. Tal delimitação justifica-se pela necessidade de manter o escopo viável dentro do cronograma da disciplina, permitindo, por conseguinte, que novas construções sejam incorporadas nas etapas seguintes sem prejuízo da arquitetura. Um programa de exemplo encontra-se em `exemplos/exemplo1.c`.

## Estrutura do repositório

```
.
├── backend/            API em Python (Flask) que conterá os analisadores
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/           Interface web servida pelo Nginx
│   ├── index.html
│   └── Dockerfile
├── config/             Arquivos de configuração
│   └── nginx.conf
├── exemplos/           Programas de exemplo em MiniC
│   └── exemplo1.c
├── docker-compose.yml
└── README.md
```

O frontend é servido pelo Nginx na porta 8080 da máquina hospedeira. As requisições destinadas a `/api/` são encaminhadas pelo próprio Nginx ao contêiner do backend, que permanece acessível apenas pela rede interna do Docker. Não há banco de dados nesta etapa, uma vez que o projeto ainda não o exige.

## Pré-requisitos

1. Git;
2. Docker Engine 24 ou superior;
3. Docker Compose v2 (comando `docker compose`).

As versões instaladas podem ser verificadas com:

```bash
docker --version
docker compose version
```

## Execução

Clonar o repositório e acessar a pasta:

```bash
git clone https://github.com/Anavalerianob/compiladores-minic.git
cd compiladores-minic
```

Construir as imagens e subir os contêineres:

```bash
docker compose up --build -d
```

Em seguida, acessar `http://localhost:8080` no navegador. A mensagem "Hello, World!" exibida na página é obtida do backend, o que comprova que frontend, backend e a comunicação entre eles estão em funcionamento.

Opcionalmente, o backend pode ser testado diretamente por meio do proxy:

```bash
curl http://localhost:8080/api/hello
```

Para acompanhar os logs:

```bash
docker compose logs -f
```

## Encerramento

Para derrubar os contêineres:

```bash
docker compose down
```

Para remover também as imagens geradas:

```bash
docker compose down --rmi all
```

## Validação de instalação limpa

Com o intuito de garantir que o projeto não dependa de configurações existentes apenas na máquina de desenvolvimento, deve-se executar o seguinte procedimento:

```bash
docker compose down --rmi all
git clone https://github.com/Anavalerianob/compiladores-minic.git teste-limpo
cd teste-limpo
docker compose build --no-cache
docker compose up -d
curl http://localhost:8080/api/hello
```

O resultado esperado do último comando é `{"mensagem":"Hello, World!"}`, e a página em `http://localhost:8080` deve exibir a mesma mensagem.
