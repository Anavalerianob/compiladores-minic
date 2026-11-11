# Materiais e métodos da etapa 4

Registro curto das decisões técnicas da análise sintática, da AST e da explicação com IA, com os critérios de avaliação definidos antes dos resultados.

## Decisões técnicas

### Estratégia do parser

Escolhi um parser descendente recursivo escrito à mão, sem ANTLR, Lark ou PLY. Há uma função por não terminal da gramática. Essa estratégia é a mais didática para o projeto: cada função espelha uma regra da gramática, o que permite registrar a ordem em que os nós são construídos (para o passo a passo da interface) e citar a regra violada em cada erro. A gramática foi escrita sem recursão à esquerda e com um token de olhar à frente (LL(1)), o que casa com o parser descendente recursivo.

### Formato da AST

Cada nó tem id, ordem de criação (em pós-ordem), tipo, rótulo, regra da gramática, papel em relação ao pai, posição em linha e coluna, índices dos tokens e atributos. A AST guarda só o que importa para o significado: não tem `;` nem chaves, e os parênteses não viram nó. O formato completo está em `ast.md`.

### Decisão sobre erros léxicos

Se o scanner encontra erros léxicos, o parser não é executado. Tokens faltando produziriam erros sintáticos sem sentido. A resposta informa isso, e a interface explica ao usuário que a análise sintática não foi executada.

### Recuperação de erros

O parser usa o modo pânico: ao encontrar um erro, registra o diagnóstico e descarta tokens até um ponto de sincronização (`;`, `}` ou o início de um item). Não registra um novo erro antes de consumir ao menos um token após a sincronização, o que evita cascata. O limite é de 20 erros por análise.

### Limites

O aninhamento é limitado a 100 níveis (parênteses, menos unário, blocos e else if somados). Ao passar disso, o parser gera um erro sintático tratado, em vez de deixar a recursão do Python estourar e virar erro 500.

### Papel da IA

A IA apenas explica. O scanner e o parser continuam produzindo tokens, AST e erros, e a análise funciona com o Ollama desligado. O backend reexecuta o scanner e o parser sobre o código recebido e monta o contexto a partir desse resultado, para que o modelo receba apenas dados produzidos pelo compilador. O modelo é o Llama 3.2 (3B), executado localmente pelo Ollama.

## Critérios de avaliação

Estes critérios foram definidos antes de medir os resultados:

1. todas as referências de AST do enunciado (precedência, associatividade, parênteses, menos unário e condicional encadeada) produzem a estrutura esperada, conferida com dicionários escritos à mão;
2. todos os casos de erro da tabela do enunciado produzem o erro esperado, com `encontrado`, `esperado`, posição, regra e trechos da mensagem conferidos;
3. a recuperação registra dois erros em linhas diferentes como dois erros, não gera cascata em um erro isolado e respeita o limite de 20 erros;
4. 150 parênteses abertos geram erro sintático, sem exceção do Python;
5. o contrato de `POST /api/analisar` preserva os campos da etapa 3 e acrescenta os blocos `lexico` e `sintatico`;
6. a interface mostra a AST navegável, funciona só com teclado e funciona em 390 pixels de largura;
7. a explicação com IA monta o contexto só com dados do compilador, trata indisponibilidade, tempo esgotado e resposta inválida, e nunca expõe endereço ou porta;
8. a análise continua funcionando com o Ollama desligado.

## Casos de teste

### Casos válidos

Declaração com e sem inicialização, lista de declaradores, `float` com literal real, atribuição, `if`, `if`/`else`, `else if`, bloco vazio, blocos aninhados, programa vazio, código só com comentários, comando único, e as expressões `2 + 3 * 4`, `10 - 3 - 2`, `8 / 4 / 2`, `(10 + 5) * 2`, `-a * 2` e `- - a`.

### Casos inválidos

`int x = 5`, `int x = 5` seguido de `int y;`, `if (x > 0 { x = 1; }`, `{ int a;`, `else { x = 1; }`, `x = 1 + * 2;`, `int if = 3;`, `x = ;`, `int a = (1 + 2;`, `if (a < b < c) { }`, `10 = x;` e `int x = 1; }`.

### Casos da IA

Extração do conteúdo da resposta; contexto com o nó, o pai, os filhos e a regra certos; código entre os marcadores `<dados>`; resposta vazia ou JSON inválido virando 502; conexão recusada virando 503 após uma única nova tentativa; tempo esgotado virando 504 sem nova tentativa; modelo ausente virando 503; alvo inexistente e pergunta longa virando 400; e a regressão de que a análise funciona com a IA indisponível.

Os números dos resultados estão em `testes.md`.
