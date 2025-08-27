#!/usr/bin/env bash
# Bash de ejemplo para correr el ETL con tus credenciales del docker-compose.
# Uso:
#   ./run_etl.sh ./salidas_parte2
#   (o) bash run_etl.sh ./salidas_parte2
# Podés sobreescribir cualquier variable exportando el ENV antes de correr.

set -euo pipefail

OUTDIR="${1:-./salidas_parte2}"

# Defaults según tu compose:
MYSQL_HOST="${MYSQL_HOST:-localhost}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-scrapper}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-6vT9pQ2sXz1L}"
MYSQL_DB="${MYSQL_DB:-repuestosDB}"

python3 "$(dirname "$0")/main.py" \
  --outdir "${OUTDIR}" \
  --host "${MYSQL_HOST}" \
  --port "${MYSQL_PORT}" \
  --user "${MYSQL_USER}" \
  --password "${MYSQL_PASSWORD}" \
  --database "${MYSQL_DB}"
