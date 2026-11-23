# Casos de teste

Defini estes casos antes de interpretar os resultados. O resultado observado veio da execução do backend do repositório sobre cada entrada, depois da etapa 4. Os casos semânticos ficam pendentes até a etapa 5.

| Id | Categoria | Entrada | Resultado esperado | Resultado observado | Status |
|---|---|---|---|---|---|
| CT-01 | Válido | int a; float b = 2.5; | Duas declarações; a segunda com literal real | Conforme esperado | Aprovado |
| CT-02 | Válido | int a, b = 2; | Dois nós de declaração | Conforme esperado | Aprovado |
| CT-03 | Válido | x = 1; | Atribuição | Conforme esperado | Aprovado |
| CT-04 | Válido | int resultado = 10 + 5 * 2; | Multiplicação abaixo da adição | ADICAO(10, MULTIPLICACAO(5, 2)) | Aprovado |
| CT-05 | Válido | int r = 20 - 5 - 3; | Associatividade à esquerda | SUBTRACAO(SUBTRACAO(20, 5), 3) | Aprovado |
| CT-06 | Válido | int r = (10 + 5) * 2; | Parênteses alteram a árvore | MULTIPLICACAO(ADICAO(10, 5), 2) | Aprovado |
| CT-07 | Válido | x = -a * 2; | Menos unário mais forte que * | MULTIPLICACAO(NEGACAO(a), 2) | Aprovado |
| CT-08 | Válido | if (a <= b) {...} else if (a > 0) {...} else {...} | Condicional encadeada | CONDICIONAL com CONDICIONAL em senao | Aprovado |
| CT-09 | Válido | { int a; { a = 1; } } | Blocos aninhados | Conforme esperado | Aprovado |
| CT-10 | Válido | if (a != b) { a = b; } | Comparação e bloco | Conforme esperado | Aprovado |
| CT-11 | Léxico | int x = 5 @ 2; | Erro em 1:11; parser não executado | Conforme esperado | Aprovado |
| CT-12 | Léxico | float y = 7.5.1; | Literal malformado em 1:11 | Conforme esperado | Aprovado |
| CT-13 | Léxico | int a; /* sem fim (em duas linhas) | Comentário não fechado em 2:1 | Conforme esperado | Aprovado |
| CT-14 | Sintático | int x = 5 | Fim do código; esperado ';' em 1:10 | Conforme esperado | Aprovado |
| CT-15 | Sintático | if (x > 0 { x = 1; } | Esperado ')' em 1:11 | Conforme esperado | Aprovado |
| CT-16 | Sintático | { int a; | Bloco não fechado; cita a linha de abertura | Conforme esperado | Aprovado |
| CT-17 | Sintático | x = 1 + * 2; | Operandos esperados; encontrado '*' | Conforme esperado | Aprovado |
| CT-18 | Sintático | else { x = 1; } | else sem if | Conforme esperado | Aprovado |
| CT-19 | Sintático | int if = 3; | Palavra reservada como nome em 1:5 | Erro correto em 1:5 e um segundo erro em 1:8 (esperado '(') | Aprovado com defeito |
| CT-20 | Sintático | if (a < b < c) { } | Comparação encadeada em 1:11 | Erro correto em 1:11 e um segundo erro em 1:14 (esperado '=') | Aprovado com defeito |
| CT-21 | Sintático | int x = 5 / int y = ; / x = 2; (três linhas) | Dois erros (falta de ; e operando ausente); linha 3 aceita | Erros em 2:1 e 2:9 | Aprovado |
| CT-22 | Semântico | x = 1; | Variável não declarada | Aceito (sem análise semântica) | Pendente (Etapa 5) |
| CT-23 | Semântico | int a; int a; | Redeclaração | Aceito | Pendente (Etapa 5) |
| CT-24 | Semântico | { int a; } a = 1; | Uso fora do escopo | Aceito | Pendente (Etapa 5) |
| CT-25 | Semântico | int x = 2.5; | Aviso de conversão de float para int | Aceito | Pendente (Etapa 5) |
| CT-26 | Borda | Código vazio | Mensagem pedindo o código (HTTP 400) | Conforme esperado | Aprovado |
| CT-27 | Borda | Apenas espaços | Mensagem de conteúdo vazio (HTTP 400) | Conforme esperado | Aprovado |
| CT-28 | Borda | Apenas comentários | Programa vazio válido | AST só com PROGRAMA | Aprovado |
| CT-29 | Borda | int a; | Comando único | Conforme esperado | Aprovado |
| CT-30 | Borda | 150 parênteses abertos | Erro de limite de aninhamento, sem exceção | Erro em 1:105, limite de 100 níveis | Aprovado |
| CT-31 | Borda | 10.001 caracteres | Limite excedido (HTTP 400) | Conforme esperado | Aprovado |
| CT-32 | Fluxo | Exemplo 7 da interface | AST completa sem erros | 56 tokens e 30 nós | Aprovado |
| CT-33 | Borda | int a = 1 $; int b = 2; | Erro léxico e parser não executado | Conforme esperado | Aprovado |
| CT-34 | IA | Explicação com o Ollama desligado | HTTP 503; análise continua | Conforme esperado (docs/testes.md) | Aprovado |

## Defeito encontrado

Os casos CT-19 (`int if = 3;`) e CT-20 (`if (a < b < c) { }`) mostram o primeiro erro certo, mas geram um segundo erro sem relação com o problema real. Depois da sincronização do modo pânico, o parser reinterpreta o resto da linha (`if` vira o início de um condicional e `c` vira o início de uma atribuição). A correção ainda está pendente; quando for feita, os dois casos voltam a ser executados e o critério de ausência de erros em cascata é conferido de novo.
