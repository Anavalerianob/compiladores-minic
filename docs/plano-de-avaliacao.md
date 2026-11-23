# Plano de avaliação

Este plano foi definido antes de executar a avaliação com pessoas. Se algum critério mudar, registro aqui a mudança e o motivo.

## Critérios

| Critério | Como verifico | Meta |
|---|---|---|
| Correção léxica | testes do scanner e CT-11 a CT-13 | 100% aprovados |
| Correção sintática e da AST | testes do parser e CT-01 a CT-10, comparando com árvores escritas à mão | 100% aprovados |
| Correção semântica | CT-22 a CT-25 | etapa 5 |
| Detecção de erros | CT-11 a CT-21 | nenhum erro em cascata |
| Clareza das mensagens e das visualizações | questionário | média de pelo menos 4 em 5 |
| Consistência entre tokens, AST e código | testes de interface | 100% aprovados |
| Usabilidade | questionário por pares, escala de 1 a 5 | média de pelo menos 4 em 5 |
| Fidelidade da IA | confiro pelo menos 16 explicações (8 exemplos, nó e erro) | proporção de explicações sem tokens, nós ou erros inventados |
| Reprodutibilidade | instalação limpa com Docker Compose | sobe e passa em `tests/implantacao.sh` |

## Testes automatizados

```bash
docker compose run --rm backend pytest -v
cd frontend && npm install && npm test
sh tests/implantacao.sh
sh tests/ia.sh
```

## Avaliação por pares

Participantes: estudantes de Computação da UFJ que cursam ou já cursaram Compiladores e, se possível, o professor da disciplina.

Roteiro (cerca de 20 minutos): analisar um exemplo, editar o código, provocar um erro léxico e um sintático, usar o passo a passo do scanner e da árvore e pedir uma explicação à IA.

Formulário no Google Forms, anônimo. Não coleta nome, e-mail nem matrícula; pergunta só se a pessoa já cursou a disciplina e qual dispositivo usou. Escala de 1 (discordo totalmente) a 5 (concordo totalmente):

1. A interface foi fácil de entender e utilizar.
2. Consegui inserir um código-fonte e executar a análise.
3. As mensagens de erro foram claras e úteis.
4. A visualização dos tokens ajudou a compreender a análise léxica.
5. A visualização da AST ajudou a compreender a estrutura do programa.
6. As explicações sobre as etapas da compilação foram úteis.
7. O passo a passo do scanner ajudou a entender como os tokens são reconhecidos.
8. A construção da AST passo a passo ajudou a entender como o parser funciona.
9. Ver a regra da gramática violada ajudou a entender e corrigir o erro sintático.
10. As explicações da IA foram coerentes com os tokens e a árvore mostrados.
11. Consegui usar o sistema no dispositivo que escolhi (computador ou celular).
12. O software contribuiu para minha compreensão sobre compiladores.

Perguntas abertas: problemas técnicos ou de usabilidade encontrados, melhorias sugeridas e comentários sobre as explicações da IA. As afirmações 7 a 11 avaliam o diferencial. A pergunta sobre a análise semântica entra quando ela existir.

Apresento os resultados com média, mediana e distribuição, e agrupo os comentários por tema. A avaliação está prevista para as etapas 5 a 7.

## Limitações

Não mede ganho de aprendizagem (sem grupo de controle nem pré e pós-teste). A amostra é pequena e de conveniência, de uma só instituição, e as respostas são autodeclaradas. As explicações da IA não são determinísticas.
