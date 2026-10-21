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
