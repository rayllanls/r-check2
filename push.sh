#!/usr/bin/env bash
# push.sh — commit e push de todas as alterações
# Uso: ./push.sh "mensagem do commit"

set -e

MSG="${1:-update}"

git add -A
git status --short

echo ""
read -p "Confirmar commit com mensagem \"$MSG\"? [s/N] " confirm
if [[ "$confirm" != "s" && "$confirm" != "S" ]]; then
  echo "Cancelado."
  exit 0
fi

git commit -m "$MSG"
git push
echo ""
echo "Enviado para o GitHub."
