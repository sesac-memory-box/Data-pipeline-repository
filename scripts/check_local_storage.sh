#!/usr/bin/env sh
set -eu

QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
MYSQL_HOST="${MYSQL_HOST:-localhost}"
MYSQL_PORT="${MYSQL_PORT:-3306}"

echo "Checking Qdrant HTTP endpoint: ${QDRANT_URL}"
if command -v curl >/dev/null 2>&1; then
  if curl -fsS "${QDRANT_URL}/healthz" >/dev/null 2>&1 || curl -fsS "${QDRANT_URL}/" >/dev/null 2>&1; then
    echo "Qdrant HTTP endpoint is reachable."
  else
    echo "Qdrant HTTP endpoint is not reachable."
  fi
else
  echo "curl is not installed; skipping Qdrant HTTP check."
fi

echo "Checking MySQL port: ${MYSQL_HOST}:${MYSQL_PORT}"
if command -v nc >/dev/null 2>&1; then
  if nc -z "${MYSQL_HOST}" "${MYSQL_PORT}" >/dev/null 2>&1; then
    echo "MySQL port is open."
  else
    echo "MySQL port is not open."
  fi
else
  echo "nc is not installed; skipping MySQL port check."
fi
