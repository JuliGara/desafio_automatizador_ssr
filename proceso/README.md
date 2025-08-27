# Automatización de Procesos (Email → ClickUp → Discord → Preparación para Boxer)

## Contexto
Algunos de los proveedores de nuestros clientes no cuentan con una página web que podamos Scrappear para obtener la lista de precios ni un programa desktop que podamos automatizar, sino que realizan el envío de listas por email. Además de esto, el equipo utiliza la herramienta “ClickUp” para la gestión del trabajo a realizar y se utiliza Discord para gestionar la comunicación institucional. Hoy en día el mail se revisa múltiples veces por dia para ver si llega una lista nueva, de llegar un mail se crea una tarjeta en ClickUp en la columna “Nueva Lista” que contenga el archivo que llego por mail, el nombre del cliente, el nombre del proveedor. Luego, la persona encargada de la limpieza de listas de precios debe revisar, múltiples veces por día, el tablero de ClickUp para ver si hay una nueva lista de precios a convertir y subir a Boxer. Con la automatización de este proceso buscamos reducir demoras, minimizar tareas repetitivas y garantizar trazabilidad.

## Objetivos
- Reducir trabajo manual y tiempos entre la llegada del email y la creación de la tarea.
- Garantizar **trazabilidad**.
- Estandarizar el **almacenamiento de adjuntos** para facilitar la limpieza y subida a Boxer.
- Notificar automáticamente en **Discord** cuando hay una nueva lista.

---

## Flujo actual (AS-IS)
1. **Persona encargada de revisar mail** revisa el inbox varias veces al día.
2. Si hay email con una lista:
   - Descarga adjunto.
   - Crea tarea en **ClickUp** (columna “Nueva Lista”) y adjunta archivo.
   - Completa **Cliente** y **Proveedor**.
3. **Persona encargada de la limpieza de listas** mira ClickUp repetidas veces, toma la tarea, limpia y sube a **Boxer**.

**Sistemas externos:** Gmail/IMAP, ClickUp, Discord, Google Drive/Storage.
---

## Propuesta de automatización
**Disparador:** Email entrante (IMAP/Gmail).

1) **Trigger (n8n – IMAP Email Trigger)**  
   - Filtro por asunto/remitente (palabras clave: “lista”, “precios”).
   - Descarga adjuntos válidos (xls/xlsx/csv/txt/pdf).

2) **Guardar adjuntos (n8n – Google Drive Upload → Share → Get link)**  
   - Ruta estandarizada: `Boxer/Listas/{cliente}/{proveedor}/{yyyy-mm-dd}/archivo.ext`.
   - Obtención de `webViewLink` para acceso rápido.

3) **Crear tarea en ClickUp (n8n – ClickUp Create Task)**  
   - Lista: **“Nueva Lista”**.  
   - Título: `[Cliente] Lista {Proveedor} - {Fecha email}`  
   - Descripción con: remitente, asunto, links a Drive, nombre de archivo.  
   - Tags: `Nueva Lista`.

4) **Notificación en Discord (n8n – HTTP Request Webhook)**  
   - Postea en `#listas-nuevas` con resumen y links a la tarea y al archivo en Drive.

---

## Seguridad / permisos
- Credenciales de n8n en **Credentials**.
- Drive: acceso sólo a la carpeta de listas.
- ClickUp: token con permisos mínimos a la lista.
- Discord: webhook sólo en canal específico.

---

## Workflow (n8n)
El archivo `n8n_workflow.json` (en esta carpeta) refleja el flujo: **Email → Drive → ClickUp → Discord**.  

---
