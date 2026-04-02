#!/usr/bin/env bash
# release.sh — cria tag e dispara o build no GitHub Actions
# Uso: ./release.sh v0.2.0

set -e

TAG="${1}"

if [[ -z "$TAG" ]]; then
  # Sugere próxima patch version baseado na última tag semântica (vX.Y.Z)
  LAST=$(git tag --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
  if [[ -z "$LAST" ]]; then
    LAST="v0.0.0"
  fi
  IFS='.' read -r major minor patch <<< "${LAST#v}"
  NEXT="v${major}.${minor}.$((patch + 1))"
  read -p "Tag para release [$NEXT]: " TAG
  TAG="${TAG:-$NEXT}"
fi

echo "Criando release $TAG..."
git tag "$TAG"
git push origin "$TAG"
echo ""
echo "Build iniciado: https://github.com/rayllanls/r-check/actions"
echo "Release:        https://github.com/rayllanls/r-check/releases/tag/$TAG"
