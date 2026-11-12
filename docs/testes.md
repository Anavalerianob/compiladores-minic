# Registro de testes

## Etapa 2 (21/10/2026)

| Funcionalidade | Tipo de teste | Comando | Resultado |
|---|---|---|---|
| Validação da entrada (backend) | Unitário | `cd backend && pytest -v` | 7 aprovados, 0 reprovados |
| Endpoints `/api/hello`, `/api/saude`, `/api/analisar` e tratamento de erros | Endpoint e regressão | `cd backend && pytest -v` | 14 aprovados, 0 reprovados |
| Tela principal, exemplos, validação e comunicação (frontend) | Interface e integração simulada | `cd frontend && npm install && npm test` | 19 aprovados, 0 reprovados |
| Interface, proxy e backend em execução | Implantação | `sh tests/implantacao.sh` | 5 aprovados, 0 reprovados |
| Fluxo completo no navegador (selecionar exemplo, analisar, entrada só com espaços) | Ponta a ponta manual em Chromium | acesso a `http://localhost:8080` | Mensagens exibidas conforme o esperado |

Total de testes automatizados: 45 aprovados e 0 reprovados.

### Falhas encontradas e correções

1. O script de testes do frontend usava `node --test tests/`, que não localizou os arquivos de teste. O comando foi corrigido para `node --test tests/interface.test.js`.
2. Na etapa 1, o frontend acessava o backend por `http://localhost:5000`, endereço que só funciona na máquina onde os contêineres rodam. A comunicação passou a ser feita pelo proxy do Nginx em `/api/`, e a rota `/hello` foi movida para `/api/hello`. O teste de regressão foi atualizado para o novo endereço.

### Limitações e pendências

1. Os testes de interface utilizam o jsdom e simulam o servidor, de modo que não substituem um teste de ponta a ponta automatizado em navegador real.
2. O teste de implantação foi executado com o backend e um proxy equivalente ao Nginx rodando localmente, pois o ambiente de desenvolvimento não tinha acesso ao Docker Hub. A execução completa via `docker compose up --build -d` deve ser repetida em ambiente limpo antes da apresentação.
3. Ainda não há testes de ponta a ponta automatizados em navegador (por exemplo, com Playwright).

## Etapa 3 (27/10/2026)

### Ambiente de execução

Durante o desenvolvimento, os testes foram executados fora dos contêineres, pois a máquina ainda não dispunha de Docker nem de curl: o backend com Python 3.14.4 em um ambiente virtual com as versões fixadas em `requirements.txt` (Flask 3.0.3 e pytest 8.3.3), e o frontend com Node.js 22.11.0 e jsdom 25.0.1. Após a instalação do Docker 29.1.3, do Docker Compose 2.40.3, do curl 8.18.0 e do Node.js 22.22.1, todos os conjuntos foram executados novamente, e os resultados abaixo correspondem a essa execução final. Os testes do backend foram executados no contêiner, com Python 3.12.16.

### Resultados

| Funcionalidade | Tipo de teste | Comando | Aprovados | Reprovados |
|---|---|---|---|---|
| Scanner: palavras reservadas, identificadores, literais, operadores, delimitadores, comentários, espaços, linha e coluna, erros, bordas e transições | Unitário | `docker compose run --rm backend pytest -v tests/test_scanner.py` | 77 | 0 |
| Validação da entrada | Unitário | `docker compose run --rm backend pytest -v` | 7 | 0 |
| Endpoints, tratamento de erros e regressão da etapa 2 | Endpoint e regressão | `docker compose run --rm backend pytest -v` | 14 | 0 |
| Integração do scanner ao endpoint: contrato completo, erro léxico com HTTP 200, código só com comentário, entrada vazia sem tokens e exceção no scanner | Endpoint | `docker compose run --rm backend pytest -v` | 5 | 0 |
| Tela principal, exemplos, validação e comunicação (etapa 2, com mocks atualizados) | Interface e regressão | `cd frontend && npm install && npm test` | 20 | 0 |
| Funções auxiliares, seção de análise, tabela, destaque, contagem, erros, passo a passo, reprodução, estados da tela e segurança | Interface | `cd frontend && npm install && npm test` | 22 | 0 |
| Interface, proxy e scanner em execução nos contêineres | Implantação | `sh tests/implantacao.sh` | 7 | 0 |

A execução completa do backend (`docker compose run --rm backend pytest -v`) resultou em 103 testes aprovados e 0 reprovados, a do frontend (`cd frontend && npm install && npm test`), em 42 aprovados e 0 reprovados, e a de implantação, em 7 verificações aprovadas e 0 reprovadas. Total: 152 verificações automatizadas aprovadas e 0 reprovadas.

O conjunto de interface da etapa 2 passou de 19 para 20 testes porque o teste de carregamento é gerado para cada exemplo, e foi acrescentado o exemplo de comentários.

### Validação em instalação limpa

Foram executados, em sequência, `docker compose down --rmi all`, `docker compose build --no-cache` e `docker compose up -d`. As duas imagens foram construídas do zero, e `docker compose ps` indicou o backend em execução com estado `healthy` e o frontend em execução com a porta `8080:80` publicada. Em seguida, `sh tests/implantacao.sh` apresentou as 7 verificações aprovadas, e `docker compose run --rm backend pytest -v` apresentou 103 testes aprovados.

A primeira tentativa falhou por permissão de acesso ao Docker (`permission denied` em `/var/run/docker.sock`), pois o usuário havia sido incluído no grupo `docker` sem iniciar uma nova sessão; também faltava o plugin `docker-buildx`. Após a instalação do plugin e a reinicialização do sistema, a sequência foi executada sem erros. Não houve alteração no código do projeto em decorrência dessa falha.

### Verificações complementares

1. Fluxo com o backend real: a interface (`index.html` e `app.js`) foi carregada no jsdom e conectada ao Flask em execução local, sem simulação do servidor. Para os cinco exemplos, a seção de análise foi exibida, o texto do código destacado coincidiu com o código enviado, e a quantidade de linhas da tabela coincidiu com a de tokens. No Exemplo 5, foram destacados os erros `7.5.1` (linha 2, coluna 15), `@` (linha 3, coluna 15) e `/*` (linha 4, coluna 1); as colunas foram conferidas manualmente, caractere a caractere.
2. Navegador real: o frontend foi servido por um servidor Python local que repassa `/api/` ao Flask, reproduzindo o comportamento do `nginx.conf`, e foi aberto no navegador Brave em modo headless, controlado pelo protocolo DevTools. Com o Exemplo 5, verificou-se: seção oculta antes da análise; mensagem com estilo de erro; 15 linhas na tabela; avanço pelo teclado (seta para a direita); seleção pelo clique na tabela; reprodução automática na velocidade rápida até o token 15, com o botão retornando a "Reproduzir"; e ausência de erros no console. Na largura de 390 pixels, o documento não apresentou rolagem horizontal e os botões de controle ocuparam a largura disponível, com altura mínima de 44 pixels. As capturas de tela foram inspecionadas visualmente.
3. Navegador real com os contêineres: o mesmo roteiro do item anterior foi repetido em `http://localhost:8080`, com o frontend servido pelo Nginx do contêiner, e produziu os mesmos resultados, inclusive as três mensagens de erro do Exemplo 5 e a ausência de erros no console.

### Falhas encontradas e correções

1. Nenhum teste automatizado falhou durante o desenvolvimento desta etapa.
2. Na inspeção das capturas de tela, observou-se que a numeração da lista de transições do passo a passo ficava sobre a borda do painel. O recuo da lista foi aumentado de 20 para 32 pixels, e os testes de interface foram executados novamente, com 42 aprovados.

### Alterações intencionais de comportamento

1. A mensagem de sucesso de `POST /api/analisar` deixou de ser "Código recebido com sucesso." e passou a descrever o resultado da análise léxica. O teste `test_analisar_codigo_valido` foi atualizado para "Análise léxica concluída sem erros: 8 token(s) reconhecido(s).", valor conferido manualmente para o código `int numero = 10;\nfloat b;` (`int`, `numero`, `=`, `10`, `;`, `float`, `b`, `;`). Os demais testes da etapa 2 permaneceram inalterados.
2. A resposta 200 passou a incluir os campos `sucesso`, `tokens` e `erros`. No frontend, a resposta simulada `respostaSucesso` foi atualizada para esse contrato, e a asserção do teste "código válido é enviado via POST em JSON para /api/analisar" passou a esperar a mensagem da análise léxica. Uma resposta 200 sem `tokens` ou `erros` passou a ser tratada como fora do contrato, o que é verificado por um teste próprio.
3. O antigo "Exemplo 4: Código com erro intencional" (`int x = ;` e `float y = 3.5`), que não continha erros léxicos, foi substituído pelo "Exemplo 4: Comentários e operadores relacionais" e pelo "Exemplo 5: Código com erros léxicos".
4. As mensagens de erro léxico seguem um formato único, iniciado por "Erro léxico na linha L, coluna C:". No caso de literal malformado, a descrição que segue esse prefixo começa por "literal numérico malformado '<trecho>'".

### Limitações e pendências

1. Os testes de interface utilizam o jsdom e simulam o servidor; a verificação em navegador real foi realizada por um script local, que controlou o navegador em modo headless, e não faz parte dos testes automatizados do repositório.
2. O arquivo `frontend/package-lock.json`, gerado pelo `npm install`, não é versionado, como na etapa 2; por isso, a versão do jsdom instalada pode variar dentro da faixa `^25.0.1`.

## Etapa 4 (11/11/2026)

### Ambiente de execução

Os testes unitários desta etapa foram executados primeiro fora dos contêineres, em um ambiente virtual com Python 3.14.4, pytest 8.3.3 e Flask 3.0.3, e no frontend com Node.js 22.22.1 e jsdom 25.0.1. Depois, o backend foi executado no contêiner, com Python 3.12, após a construção das imagens do zero. A integração real do Ollama e a demonstração no navegador ainda não foram executadas; estão listadas como pendências.

### Validação em instalação limpa

Foram executados, em sequência, `docker compose build --no-cache` e `docker compose up -d`. As duas imagens foram construídas do zero, e `docker compose ps` indicou o backend em execução com estado `healthy`, o frontend com a porta `8080:80` publicada e o contêiner `ollama` em execução com a porta 11434 apenas interna (não publicada no host). Em seguida, `sh tests/implantacao.sh` apresentou as 9 verificações aprovadas, incluindo as duas novas (a análise de `int resultado = 10 + 5 * 2;` contém `MULTIPLICACAO` e a de `int x = 5` contém `ERRO_SINTATICO`), e `docker compose run --rm backend pytest -q` apresentou 172 testes aprovados e 1 pulado, com Python 3.12.

Sem o modelo `llama3.2` baixado, uma requisição a `POST /api/ia/explicar` respondeu HTTP 503 (assistente indisponível), e `POST /api/analisar` continuou respondendo normalmente. Isso confirma que a análise não depende do Ollama. O download do modelo, o `sh tests/ia.sh` e a integração real não foram executados por escolha, para não baixar os cerca de 4 GB do modelo nesta máquina.

### Resultados

| Funcionalidade | Tipo de teste | Comando | Aprovados | Reprovados |
|---|---|---|---|---|
| Scanner (regressão da etapa 3) | Unitário | `pytest -v tests/test_scanner.py` | 77 | 0 |
| Parser: construções válidas, estrutura da AST das referências, precedência, associatividade, posições, ordem de criação, ids, casos de erro, recuperação, limite de aninhamento e integração com o scanner | Unitário | `pytest -v tests/test_parser.py` | 47 | 0 |
| API: validação, endpoints, contrato da etapa 3 preservado e contrato da etapa 4 com `lexico` e `sintatico` | Endpoint e regressão | `pytest -v tests/test_api.py` | 30 | 0 |
| IA: extração do conteúdo, contexto correto, 400, 502, 503, 504, mensagens sem endereço e regressão da análise com IA indisponível | Unitário com mock | `pytest -v tests/test_ia.py` | 18 | 0 |
| Interface: léxica da etapa 3 (com mocks atualizados), AST navegável, seleção de nós, filtro, exportação, passo a passo, erros sintáticos, distinção léxico e sintático, árvore grande, explicações com IA e abas do layout | Interface | `cd frontend && npm install && npm test` | 79 | 0 |

A execução completa do backend (`pytest -v`) resultou em 172 testes aprovados, 0 reprovados e 1 pulado (a integração real do Ollama, pulada por padrão). O frontend (`npm test`) resultou em 79 testes aprovados e 0 reprovados. Total automatizado desta execução: 251 testes aprovados, 0 reprovados e 1 pulado.

O conjunto de interface passou de 42 para 79 testes: 3 a mais porque o teste de carregamento é gerado para cada exemplo e foram acrescentados três exemplos, mais os testes da AST, da IA e, por fim, 8 testes das abas do novo layout. O conjunto de API passou de 26 para 30: quatro testes novos do contrato da etapa 4.

### Reorganização da interface

A interface foi reorganizada em duas colunas (entrada fixa à esquerda, resultados à direita) e os resultados foram divididos em abas: Tokens, Árvore (AST), Erros (com contador no nome) e Professor IA. As abas usam `role="tablist"`, `role="tab"`, `aria-selected`, troca por clique e pelas setas do teclado; depois de analisar, abre automaticamente a aba Erros quando há erro e a aba Árvore quando não há. Foi só mudança de layout: todos os IDs e comportamentos anteriores foram mantidos, por isso os 71 testes existentes continuaram passando sem alteração, e foram acrescentados 8 testes das abas (troca por clique, troca por teclado, aba automática após a análise, contador de erros e estado inicial com placeholder). Nenhuma biblioteca externa foi adicionada.

### Alterações intencionais de contrato

1. A mensagem de `POST /api/analisar` mudou. Para um código válido sem erros, deixou de ser "Análise léxica concluída sem erros: N token(s) reconhecido(s)." e passou a ser "Análise léxica e sintática concluídas sem erros: N token(s) e M nó(s) na AST." (M é o número de nós da AST, conferido à mão). Com erro sintático, a mensagem é "Análise léxica sem erros; análise sintática com K erro(s).". Com erro léxico, a mensagem da etapa 3 passou a terminar com "A análise sintática não foi executada.". Os testes `test_analisar_codigo_valido`, `test_analisar_contrato_completo` e `test_analisar_erro_lexico_retorna_200_com_sucesso_falso` foram atualizados; o campo `sucesso` do topo continua se referindo à análise léxica.
2. A resposta 200 passou a incluir os blocos `lexico` e `sintatico`. No frontend, as respostas simuladas `respostaSucesso` e `respostaComErro` foram atualizadas para o novo contrato, e a asserção da mensagem de sucesso foi ajustada.
3. A indicação da fase na interface deixou de ser "Fase disponível: análise léxica (scanner)" e passou a "Fases disponíveis: análise léxica (scanner) e análise sintática (parser e AST)". O teste de estado inicial da interface foi atualizado.
4. A lista de erros léxicos ganhou um botão de explicação com IA por erro. Os dois testes que comparavam o texto do item inteiro passaram a comparar o parágrafo da mensagem, e um deles passou a verificar a presença do botão.

### Falhas encontradas e correções

1. No parser, a mensagem de `;` ausente lia o nome do declarador em um formato de tupla antigo e gerava `KeyError`. Corrigi o acesso ao dicionário do nó antes de registrar os testes.
2. O teste de reprodução do passo a passo da AST chamava o temporizador falso uma vez a mais e estourava quando a reprodução já tinha parado. Passei a chamar enquanto houver uma função agendada.
3. Dois testes de interface da etapa 3 verificavam o texto exato do item de erro léxico; com o novo botão de IA, passaram a verificar o parágrafo da mensagem.

### Limitações e pendências

1. O download do modelo `llama3.2`, o `sh tests/ia.sh`, a integração real do Ollama (`OLLAMA_INTEGRACAO=1`) e a verificação de persistência do volume após `docker compose down` e `up` ainda não foram executados; dependem de baixar cerca de 4 GB do modelo. O endpoint da IA já foi verificado indiretamente: sem o modelo, responde HTTP 503 e não afeta a análise.
2. A demonstração no navegador (digitar o código, ver a AST, selecionar a multiplicação, pedir a explicação com IA e, depois, pedir a explicação de um erro sintático) ainda não foi feita com os contêineres em execução.
3. Os testes de interface continuam usando o jsdom e simulam o servidor, inclusive o endpoint da IA; não substituem testes de ponta a ponta em navegador real.
