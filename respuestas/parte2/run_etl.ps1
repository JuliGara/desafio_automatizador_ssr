Param(
  [string]$Outdir = ".\salidas_parte2",
  [string]$DbHost = "localhost",
  [int]$Port = 3306,
  [string]$User = "scrapper",
  [string]$Password = "6vT9pQ2sXz1L",
  [string]$Database = "repuestosDB"
)

# Resolver carpeta del script
$ScriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$etl = Join-Path $ScriptRoot "main.py"
$req = Join-Path $ScriptRoot "requirements.txt"

# Instalar deps
python -m pip install -r $req

# Ejecutar ETL
python $etl `
  --outdir $Outdir `
  --host $DbHost `
  --port $Port `
  --user $User `
  --password $Password `
  --database $Database
