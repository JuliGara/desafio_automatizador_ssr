from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

# ---------------- CLI ----------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ETL Parte 2 - SQL puro + pandas (esquema exacto de la consigna)")
    p.add_argument("--outdir", required=True, help="Carpeta de salida para los CSVs")
    p.add_argument("--host", default=os.getenv("MYSQL_HOST", "localhost"))
    p.add_argument("--port", type=int, default=int(os.getenv("MYSQL_PORT", "3306")))
    p.add_argument("--user", default=os.getenv("MYSQL_USER", "root"))
    p.add_argument("--password", default=os.getenv("MYSQL_PASSWORD", ""))
    p.add_argument("--database", default=os.getenv("MYSQL_DB", "boxer"))
    return p.parse_args()

def ensure_outdir(path: str | Path) -> Path:
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    return out

def make_engine(args):
    url = f"mysql+pymysql://{args.user}:{args.password}@{args.host}:{args.port}/{args.database}?charset=utf8mb4"
    return create_engine(url, pool_pre_ping=True)

def to_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"[OK] CSV -> {path} ({len(df):,} filas)")

# Autofix cuyo precio NO se actualizó en el último mes
SQL_AUTOFIX_NO_ACT = """
SELECT
  r.id                AS repuesto_id,
  r.codigo            AS codigo,
  r.descripcion       AS descripcion,
  m.nombre            AS marca,
  p.nombre            AS proveedor,
  r.precio            AS precio_actual,
  a.fecha             AS fecha_ultima_actualizacion
FROM Repuesto r
JOIN Proveedor p          ON p.id = r.proveedor_id
LEFT JOIN Marca m         ON m.id = r.id_marca
LEFT JOIN Actualizacion a ON a.id = r.id_ultima_actualizacion
WHERE UPPER(p.nombre) = 'AUTOFIX'
  AND ( a.fecha IS NULL OR DATE(a.fecha) < DATE_SUB(CURDATE(), INTERVAL 1 MONTH) )
ORDER BY r.precio DESC, r.id ASC;
"""

# +15% para marcas específicas
SQL_INC_15 = """
SELECT
  r.id                      AS repuesto_id,
  r.codigo                  AS codigo,
  r.descripcion             AS descripcion,
  m.nombre                  AS marca,
  p.nombre                  AS proveedor,
  r.precio                  AS precio_actual,
  ROUND(r.precio * 1.15, 2) AS precio_propuesto_15
FROM Repuesto r
JOIN Marca m         ON m.id = r.id_marca
LEFT JOIN Proveedor p ON p.id = r.proveedor_id
WHERE UPPER(m.nombre) IN ('ELEXA','BERU','SH','MASTERFILT','RN')
ORDER BY m.nombre, r.codigo;
"""

# +30% para AutoRepuestos Express y Automax con 50k < precio < 100k
SQL_RECARGO_30 = """
SELECT
  r.id                      AS repuesto_id,
  r.codigo                  AS codigo,
  r.descripcion             AS descripcion,
  m.nombre                  AS marca,
  p.nombre                  AS proveedor,
  r.precio                  AS precio_actual,
  ROUND(r.precio * 1.30, 2) AS precio_con_recargo_30
FROM Repuesto r
JOIN Proveedor p ON p.id = r.proveedor_id
LEFT JOIN Marca m ON m.id = r.id_marca
WHERE UPPER(p.nombre) IN ('AUTOREPUESTOS EXPRESS','AUTOMAX')
  AND r.precio > 50000 AND r.precio < 100000
ORDER BY p.nombre, r.precio DESC;
"""

# Resumen por proveedor
SQL_RESUMEN_PROV = """
SELECT
  t.proveedor_id,
  t.proveedor,
  t.total_repuestos,
  t.sin_descripcion,
  r.id          AS repuesto_id_mas_caro,
  r.codigo      AS codigo_mas_caro,
  r.descripcion AS descripcion_mas_caro,
  r.precio      AS precio_mas_caro
FROM (
  SELECT
    p.id AS proveedor_id,
    p.nombre AS proveedor,
    COUNT(*) AS total_repuestos,
    SUM(CASE WHEN r.descripcion IS NULL OR TRIM(r.descripcion) = '' THEN 1 ELSE 0 END) AS sin_descripcion,
    MAX(r.precio) AS precio_mas_caro
  FROM Repuesto r
  JOIN Proveedor p ON p.id = r.proveedor_id
  GROUP BY p.id, p.nombre
) t
JOIN Repuesto r
  ON r.proveedor_id = t.proveedor_id AND r.precio = t.precio_mas_caro
ORDER BY t.proveedor;
"""

# Promedio por marca dentro de cada proveedor
SQL_PROM_MARCA_EN_PROV = """
SELECT
  p.id     AS proveedor_id,
  p.nombre AS proveedor,
  m.id     AS marca_id,
  m.nombre AS marca,
  ROUND(AVG(r.precio), 2) AS precio_promedio
FROM Repuesto r
JOIN Proveedor p ON p.id = r.proveedor_id
JOIN Marca m     ON m.id = r.id_marca
GROUP BY p.id, p.nombre, m.id, m.nombre
ORDER BY p.nombre, m.nombre;
"""

# Main 

def main():
    args = parse_args()
    outdir = ensure_outdir(args.outdir)
    engine = make_engine(args)

    df_autofix = pd.read_sql(SQL_AUTOFIX_NO_ACT, con=engine)
    to_csv(df_autofix, outdir / "autofix_no_actualizados_ultimo_mes.csv")

    df_inc15 = pd.read_sql(SQL_INC_15, con=engine)
    to_csv(df_inc15, outdir / "precio_propuesto_15_marcas_seleccionadas.csv")

    df_recargo = pd.read_sql(SQL_RECARGO_30, con=engine)
    to_csv(df_recargo, outdir / "recargo_30_autorepuestos_automax_50k_100k.csv")

    df_resumen = pd.read_sql(SQL_RESUMEN_PROV, con=engine)
    df_resumen.insert(0, "seccion", "resumen_proveedor")

    df_prom_en_prov = pd.read_sql(SQL_PROM_MARCA_EN_PROV, con=engine)
    df_prom_en_prov.insert(0, "seccion", "promedio_por_marca_en_proveedor")

    # Normalizamos columnas para concatenar
    cols = [
        "seccion",
        "proveedor_id", "proveedor",
        "total_repuestos", "sin_descripcion",
        "repuesto_id_mas_caro", "codigo_mas_caro", "descripcion_mas_caro", "precio_mas_caro",
        "marca_id", "marca", "precio_promedio"
    ]

    # completar faltantes
    df_resumen = df_resumen.assign(marca_id=None, marca=None, precio_promedio=None)[cols]
    df_prom_en_prov = df_prom_en_prov.assign(
        total_repuestos=None, sin_descripcion=None,
        repuesto_id_mas_caro=None, codigo_mas_caro=None, descripcion_mas_caro=None, precio_mas_caro=None
    )[cols]

    df_unico = pd.concat([df_resumen, df_prom_en_prov], ignore_index=True)
    to_csv(df_unico, outdir / "resumen_proveedor.csv")

    print("\nHecho. CSVs generados en:", outdir.resolve())

if __name__ == "__main__":
    main()
