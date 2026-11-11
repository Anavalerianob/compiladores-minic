# Fluxogramas do processamento

Este documento registra, para o artigo da disciplina, o fluxo do processamento de um programa no MiniC Analisador e o fluxo da explicação com IA.

## Processamento de um programa

Do código informado até a apresentação dos resultados. A análise semântica aparece como etapa 5, ainda não implementada.

```mermaid
flowchart TD
    A[Código informado na interface] --> B[Validação da entrada]
    B --> C{Entrada válida?}
    C -- Não --> R[Mostra mensagem de validação; HTTP 400]
    C -- Sim --> D[Análise léxica: scanner]
    D --> E{Há erros léxicos?}
    E -- Sim --> F[Mostra erros léxicos; análise sintática não é executada]
    E -- Não --> G[Análise sintática: parser]
    G --> H{Há erros sintáticos?}
    H -- Sim --> I[Mostra erros sintáticos com a regra violada; AST nula]
    H -- Não --> J[Construção da AST]
    J --> K[Análise semântica - etapa 5, não implementada]
    K --> L[Apresentação dos resultados: tokens, AST e erros]
    F --> L
    I --> L
```

## Explicação com IA

Fluxo separado, acionado quando o usuário pede uma explicação. A análise não depende dele.

```mermaid
flowchart TD
    A[Usuário pede explicação de token, nó, erro ou pergunta] --> B[Frontend chama POST /api/ia/explicar]
    B --> C[Backend reexecuta scanner e parser sobre o código]
    C --> D[Monta o contexto só com dados do compilador]
    D --> E{Modelo instalado no Ollama?}
    E -- Não --> F[HTTP 503: assistente indisponível]
    E -- Sim --> G[Envia o contexto ao Ollama - api/chat]
    G --> H{Resposta?}
    H -- Tempo esgotado --> I[HTTP 504]
    H -- Vazia ou inválida --> J[HTTP 502]
    H -- Conteúdo válido --> K[HTTP 200 com a explicação]
    K --> L[Interface exibe o texto com o aviso de que pode conter erros]
    F --> M[Interface mostra mensagem clara; a análise continua funcionando]
    I --> M
    J --> M
```
