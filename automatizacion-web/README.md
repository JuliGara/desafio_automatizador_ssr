# Automatización Web — Descarga, Normalización y Subida de Listas

## Introducción

Este proceso automatiza el ciclo completo para 3 proveedores publicados en la web:

1) **Descarga** dinámica de listas de precios desde `https://desafiodataentryait.vercel.app/` (Selenium).  
2) **Normalización** a un formato estándar (Pandas):  
   - Columnas **CODIGO, DESCRIPCIÓN, MARCA, PRECIO**.  
   - Precios normalizados con punto decimal y sin separador de miles.  
   - Reglas específicas por proveedor (ej. concatenar “Descripción + Rubro”, unificar hojas, etc.).  
3) **Subida** del archivo final a la **API** mediante `POST multipart/form-data` con el campo `file`.

El flujo reconoce de forma **automática** si la descarga es directa, si requiere **login**, o si necesita **marcar checkboxes** y luego presionar un botón de descarga en la página del proveedor.

---

## Estructura rápida

```
automatizacion-web/
├─ data/
│  ├─ raw/         # descargas originales (xlsx/csv)
│  └─ processed/   # xlsx normalizados listos para API
├─ web_pipeline/
│  ├─ downloader.py  # Selenium: descubre tarjetas y descarga
│  ├─ processor.py   # Pandas: normaliza por proveedor
│  └─ uploader.py    # requests: POST a la API
├─ main.py           # orquestación (descargar → procesar → subir)
├─ credentials.json  # base_url + credenciales (opcional)
└─ requirements.txt
```

---

## Requisitos

- **Windows** + **PowerShell** (comandos abajo).  
- **Python 3.10+**  
- **Google Chrome** instalado (el script usa `webdriver-manager` para el driver).  

## Configuración de `credentials.json`

Crear el archivo en la raíz de `automatizacion-web/`:

```json
{
  "base_url": "BASEURL",
  "username": "USERNAME",
  "password": "PASSWORD"
}
```

- Si un proveedor **no** requiere login, igual funcionará: el flujo intenta descargar directo y solo usa credenciales si detecta pantalla de login.  
- Podés dejar `username`/`password` como `""` (vacío) si querés forzar comportamiento “sin login”.

---

## Ejecución local (PowerShell)

```powershell

# Crear y activar venv
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Primer corrida (headless = navegador oculto). Descarga + procesa
python .\main.py --credentials .\credentials.json --headless true

# Con navegador visible (útil para ver la interacción con login/checkboxes)
python .\main.py --credentials .\credentials.json --headless false

# Subir los XLSX normalizados a la API
python .\main.py --credentials .\credentials.json --headless true --upload true

# (Opcional) Cambiar carpetas de salida / API
python .\main.py `
  --credentials .\credentials.json `
  --download_dir .\data
aw `
  --outdir .\data\processed `
  --headless true `
  --upload true `
  --api_url https://desafio.somosait.com/api/upload/
```

**Flags disponibles**
- `--credentials` (ruta a `credentials.json`)  
- `--download_dir` (descargas originales)  
- `--outdir` (normalizados)  
- `--headless true|false` (Chrome visible u oculto)  
- `--upload true|false` (enviar a API)  
- `--api_url` (sobrescribe URL de la API si querés probar otra)

---

## Archivos generados

- **Descargas originales**: `data/raw/`  
- **Normalizados**: `data/processed/`  
  - `autorepuestos_express_YYYY-MM-DD.xlsx`  
  - `autofix_YYYY-MM-DD.xlsx`  
  - `mundo_repcar_YYYY-MM-DD.xlsx`
