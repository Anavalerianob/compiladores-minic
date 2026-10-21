#!/bin/sh
# Teste de implantacao: verifica se os servicos subiram e se comunicam.
# Uso: com os conteineres rodando, executar "sh tests/implantacao.sh"

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

codigo=$(curl -s -o /dev/null -w "%{http_code}" "$URL/")
verificar "Interface acessivel" "$codigo" "200"

codigo=$(curl -s -o /dev/null -w "%{http_code}" "$URL/app.js")
verificar "Script da interface acessivel" "$codigo" "200"

codigo=$(curl -s -o /dev/null -w "%{http_code}" "$URL/api/saude")
verificar "Backend responde via proxy" "$codigo" "200"

codigo=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d '{"codigo":"int numero = 10;"}' "$URL/api/analisar")
verificar "Envio de codigo valido" "$codigo" "200"

codigo=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d '{"codigo":""}' "$URL/api/analisar")
verificar "Rejeicao de codigo vazio" "$codigo" "400"

echo ""
if [ "$FALHAS" -eq 0 ]; then
  echo "Todos os testes de implantacao passaram."
else
  echo "$FALHAS teste(s) falharam."
  exit 1
fi
