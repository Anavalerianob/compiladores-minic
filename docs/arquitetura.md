# Arquitetura

Três serviços no Docker Compose. Só o frontend publica porta (8080); o backend (5000) e o Ollama (11434) ficam na rede interna. O backend reexecuta o scanner e o parser antes de chamar o modelo, para que a IA só receba dados produzidos pelo compilador, e não o que vem do navegador.

```mermaid
flowchart TB
    UI["Navegador do estudante<br/>index.html e app.js: editor, exemplos<br/>e abas Tokens, Árvore, Erros e Professor IA"]
    NG["Contêiner frontend: Nginx<br/>porta 8080 publicada<br/>arquivos estáticos e proxy de /api/"]
    subgraph BE["Backend (Flask)"]
      AP["app.py<br/>/api/analisar e /api/ia/explicar"]
      VA["validacao.py<br/>validação da entrada"]
      SC["scanner.py<br/>AFD escrito à mão"]
      PA["parser.py<br/>descendente recursivo e AST"]
      IA["ia.py<br/>contexto e chamada ao modelo"]
    end
    LM["Contêiner ollama: Llama 3.2 (3B)<br/>porta 11434 interna, volume ollama_data"]
    UI -- "HTTP e JSON" --> NG
    NG -- "proxy /api/" --> AP
    AP --> VA
    AP --> SC
    SC -- "tokens" --> PA
    AP --> IA
    IA -- "reexecuta scanner e parser" --> SC
    IA -- "POST /api/chat" --> LM
```

## Fluxo do processamento

As caixas tracejadas (análise semântica e tabela de símbolos) ainda não estão implementadas; entram na etapa 5.

```mermaid
flowchart TD
    A["Usuário insere ou seleciona um código-fonte"] --> B["Validação da entrada (frontend e backend)"]
    B --> C{"Entrada válida?"}
    C -- "Não" --> R["Mensagem de validação (HTTP 400)"]
    C -- "Sim" --> D["Análise léxica: scanner (Etapa 3)"]
    D --> E["Tokens e erros léxicos"]
    E --> F{"Há erros léxicos?"}
    F -- "Sim" --> G["Parser não é executado; motivo informado ao usuário"]
    F -- "Não" --> H["Análise sintática: parser descendente recursivo (Etapa 4)"]
    H --> I{"Há erros sintáticos?"}
    I -- "Sim" --> J["Erros sintáticos com esperado, encontrado e regra violada; AST nula"]
    I -- "Não" --> K["AST com posições e ordem de construção"]
    K -.-> L["Análise semântica (Etapa 5, não implementada)"]
    L -.-> M["Tabela de símbolos e erros semânticos (Etapa 5, não implementada)"]
    G --> P["Apresentação didática na interface: tokens, AST, erros"]
    J --> P
    K --> P
    M -.-> P
    P --> Q["Opcional: explicação com IA local (Ollama e Llama 3.2)"]
    classDef pend fill:#f3f3f3,stroke:#888,stroke-dasharray: 5 5,color:#555
    class L,M pend
```
