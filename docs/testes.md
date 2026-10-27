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
