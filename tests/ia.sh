#!/bin/sh
# Teste manual da IA (Ollama). Exige os conteineres rodando e o llama3.2 baixado.
# Uso: sh tests/ia.sh
# Como a resposta do modelo pode demorar na CPU, este teste usa um tempo limite maior.

URL="http://localhost:8080"
FALHAS=0

verificar() {
  if [ "$2" = "$3" ]; then
    echo "OK    $1"
  else
    echo "FALHA $1 (esperado: $3, obtido: $2)"
    FALHAS=$((FALHAS + 1))
  fi
}

contem() {
  if printf '%s' "$1" | grep -q "$2"; then echo "sim"; else echo "nao"; fi
}

# 1. Conteiner do Ollama em execucao.
estado=$(docker compose ps --status running ollama 2>/dev/null | grep -c ollama)
verificar "Conteiner ollama em execucao" "$estado" "1"

# 2. Modelo llama3.2 instalado.
lista=$(docker compose exec -T ollama ollama list 2>/dev/null)
verificar "Modelo llama3.2 instalado" "$(contem "$lista" 'llama3.2')" "sim"

# 3. Endpoint de explicacao responde com uma explicacao nao vazia.
corpo=$(curl -s --max-time 150 -X POST -H "Content-Type: application/json" \
  -d '{"tipo":"NO_AST","codigo":"int resultado = 10 + 5 * 2;","alvo":4}' \
  "$URL/api/ia/explicar")
verificar "Explicacao gerada por IA" "$(contem "$corpo" '"geradoPorIA":true')" "sim"
vazia=$(printf '%s' "$corpo" | grep -c '"explicacao":""')
verificar "Explicacao nao vazia" "$vazia" "0"

echo ""
if [ "$FALHAS" -eq 0 ]; then
  echo "Todos os testes de IA passaram."
else
  echo "$FALHAS teste(s) de IA falharam."
  exit 1
fi
