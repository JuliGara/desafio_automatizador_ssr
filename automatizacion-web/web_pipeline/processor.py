import os, re
from datetime import datetime
import pandas as pd

# Config 
REQUIRED_HEADERS = ["CODIGO", "DESCRIPCIÓN", "MARCA", "PRECIO"]

# Utilidades básicas 
def _norm(s: str) -> str:
    """Normaliza string: minúsculas y solo [a-z0-9]."""
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

def normalize_price(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = re.sub(r"[^0-9,.-]", "", str(v).strip())
    if s.count(",") == 1 and s.count(".") > 1:
        s = s.replace(".", "").replace(",", ".")
    elif s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except:
        return None


# Lectura inteligente de XLSX/CSV sin header y detección de fila de encabezados
def smart_read(path: str, sheet=None) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(path, sheet_name=sheet if sheet is not None else 0, header=None)
    else:
        raw = None
        for enc in ("utf-8-sig", "latin-1"):
            try:
                raw = pd.read_csv(path, header=None, sep=None, engine="python", encoding=enc)
                break
            except Exception:
                continue
        if raw is None:
            raw = pd.read_csv(path, header=None, sep=None, engine="python")
        df = raw

    best_row, best_score = None, -1
    lim = min(40, len(df))
    for i in range(lim):
        row = df.iloc[i].astype(str).str.lower()
        score = sum(any(k in cell for k in ["codigo","código","descr","precio","marca","rubro","importe","cod"]) for cell in row)
        if score > best_score:
            best_score, best_row = score, i

    if best_row is None:
        df.columns = [str(c) for c in df.iloc[0]]
        df = df.iloc[1:].reset_index(drop=True)
    else:
        cols = df.iloc[best_row].astype(str).tolist()
        df = df.iloc[best_row+1:].reset_index(drop=True)
        df.columns = cols
    return df

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")

# Guardado de XLSX con nombre normalizado y fecha
def save_xlsx(df: pd.DataFrame, outdir: str, slug: str) -> str:
    os.makedirs(outdir, exist_ok=True)
    slug = re.sub(r"(?i)^#?download[-_]?button[-_]?", "", str(slug).strip())
    slug = slugify(slug)
    out = os.path.join(outdir, f"{slug}_{datetime.now().strftime('%Y-%m-%d')}.xlsx")
    df.to_excel(out, index=False)
    return out

# Busca columna por nombre, case-insensitive ---
def _get_col(df: pd.DataFrame, name: str) -> str | None:
    target = str(name).strip().lower()
    lookup = {str(c).strip().lower(): c for c in df.columns}
    return lookup.get(target)

# Asegura headers requeridos y orden
def _force_required_headers(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for c in df.columns:
        k = _norm(c)
        if k == "codigo":                 rename[c] = "CODIGO"
        elif k in ("descripcion","descripción"): rename[c] = "DESCRIPCIÓN"
        elif k == "marca":                rename[c] = "MARCA"
        elif k == "precio":               rename[c] = "PRECIO"
    if rename:
        df = df.rename(columns=rename)
    for h in REQUIRED_HEADERS:
        if h not in df.columns:
            df[h] = ""
    return df[REQUIRED_HEADERS]

# Procesadores por Autorepuestos Express XLSX 
def process_autorepuestos_express(path: str) -> pd.DataFrame:
    df = smart_read(path)

    code  = _get_col(df, "codigo proveedor")
    desc  = _get_col(df, "descripcion")
    rubro = _get_col(df, "rubro")
    price = _get_col(df, "precio de lista")
    brand = _get_col(df, "marca")

    # columnas mínimas
    if not all([code, desc, price]):
        return _force_required_headers(pd.DataFrame(columns=REQUIRED_HEADERS))

    out = pd.DataFrame()
    out["CODIGO"] = df[code].astype(str).str.strip()

    base = df[desc].astype(str).fillna("").str.strip()
    if rubro:
        base = (base + " - " + df[rubro].astype(str).fillna("").str.strip()).str.strip(" -")

    out["DESCRIPCIÓN"] = base.str.slice(0, 100)
    out["MARCA"] = df[brand].astype(str).str.strip() if brand else ""
    out["PRECIO"] = df[price].apply(normalize_price)
    out = out[out["PRECIO"].notna()]
    return _force_required_headers(out)

# Procesadores por AutoFix XLSX con múltiples hojas
def process_autofix(path: str) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    frames = []
    for sn in xl.sheet_names:
        try:
            df = smart_read(path, sheet=sn)

            # Renombrado por sinónimos
            rename = {}
            for c in df.columns:
                k = _norm(c)
                if k.startswith("codigo"): rename[c] = "CODIGO"
                elif k in ("descr"): rename[c] = "DESCR"
                elif k in ("descr2"): rename[c] = "DESCR2"
                elif k in ("precio"): rename[c] = "PRECIO"
                elif k in ("codrub"): rename[c] = "CODRUB"
            if rename:
                df = df.rename(columns=rename)

            # Columnas
            code  = "CODIGO" if "CODIGO" in df.columns else next((c for c in df.columns if _norm(c).startswith("codigo")), None)
            d1    = "DESCR"  if "DESCR"  in df.columns else next((c for c in df.columns if _norm(c).startswith("descr")), None)
            price = "PRECIO" if "PRECIO" in df.columns else next((c for c in df.columns if _norm(c).startswith("precio") or _norm(c)=="importe"), None)
            d2    = "DESCR2" if "DESCR2" in df.columns else next((c for c in df.columns if _norm(c) in ("descr2","descripcion2","descrip2")), None)
            codrb = "CODRUB" if "CODRUB" in df.columns else next((c for c in df.columns if _norm(c) in ("codrub","codrubro","rubro","rub")), None)

            if not code or not d1 or not price:
                continue

            desc = df[d1].astype(str).fillna("").str.strip()
            if d2 and d2 in df.columns:
                desc = (desc + " " + df[d2].astype(str).fillna("").str.strip()).str.strip()
            if codrb and codrb in df.columns:
                desc = (desc + " - " + df[codrb].astype(str).fillna("").str.strip()).str.strip(" -")

            tmp = pd.DataFrame({
                "CODIGO": df[code].astype(str).fillna("").str.strip(),
                "DESCRIPCIÓN": desc.str.slice(0, 100),
                "MARCA": sn,
                "PRECIO": df[price].apply(normalize_price)
            })
            pre = len(tmp)
            tmp = tmp[(tmp["CODIGO"] != "") & (tmp["DESCRIPCIÓN"] != "") & (tmp["PRECIO"].notna())]
            if len(tmp):
                frames.append(tmp)
        except Exception as e: pass

    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=REQUIRED_HEADERS)
    return _force_required_headers(out)

# Procesadores por Mundo Repcar CSV
def process_mundo_repcar(path: str) -> pd.DataFrame:
    df = smart_read(path)  # CSV

    # código: intenta primero 'codigo articulo', si no, 'cod fabrica'
    code = _get_col(df, "codigo articulo") or _get_col(df, "cod fabrica")

    brand = _get_col(df, "marca")
    desc  = _get_col(df, "descripcion")
    price = _get_col(df, "importe")
    rubro = _get_col(df, "rubro")  # opcional

    if not all([code, desc, price]):
        return _force_required_headers(pd.DataFrame(columns=REQUIRED_HEADERS))

    out = pd.DataFrame()
    out["CODIGO"] = df[code].astype(str).str.strip()

    d = df[desc].astype(str).fillna("").str.strip()
    if rubro:
        d = (d + " - " + df[rubro].astype(str).fillna("").str.strip()).str.strip(" -")
    out["DESCRIPCIÓN"] = d.str.slice(0, 100)

    out["MARCA"] = df[brand].astype(str).str.strip() if brand else ""
    out["PRECIO"] = df[price].apply(normalize_price)
    out = out[out["PRECIO"].notna()]
    return _force_required_headers(out)

# Selección y fachada 
def processor_for(name: str):
    s = slugify(name)
    if "autofix" in s:                            return process_autofix
    if "mundo" in s or "repcar" in s:             return process_mundo_repcar
    if "autorepuestos" in s or "express" in s:    return process_autorepuestos_express
    return process_autorepuestos_express  # default

# Procesa según proveedor, normaliza headers y guarda XLSX final.
def process_and_save(provider_name: str, input_path: str, outdir: str) -> str:
    proc = processor_for(provider_name)
    df   = proc(input_path)
    return save_xlsx(df, outdir, provider_name)
