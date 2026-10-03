# 🏛️ Manual de Usuario: Cockpit Soberano de Telemetría, Límites y LLMOps (v3.0)

Bienvenido al manual operativo del **Cockpit Soberano de Telemetría y Límites** para el ecosistema Zerops y AstroBranding. Este motor opera bajo una premisa inquebrantable: **cero consumo de tokens LLM de Gemini/Antigravity**, **ejecución 100% autónoma en TypeScript/Bun**, **cero datos asumidos o alucinados**, y **cero consumo de memoria RAM en reposo (0 MB idle)**.

---

## 1. Modos de Uso y Acceso

El Cockpit ofrece dos canales de operación complementarios:

1. **Modo Conversacional / CLI Efímero (`cockpit-status`)**: 
   - Ejecución instantánea en sub-segundo (~500ms).
   - Emite el reporte consolidado en la terminal o al chat de Antigravity (AGY) y finaliza de inmediato liberando el 100% de la memoria RAM.
   - Puede invocarse directamente vía Bash, cron o scripts sin requerir intervención de AGY ni consumir tokens de Gemini.
2. **Modo Dashboard Web Visual (`cockpit-web`)**:
   - Micro-servidor HTTP en Bun en el puerto `3050`, expuesto de forma segura por el proxy reverso Nginx en el puerto `8080`.
   - **URL de Acceso Global**: `https://zcp-252-8080.ny1.zerops.app/cockpit/`
   - Interfaz gráfica moderna con Tailwind CSS en Dark Mode nativo.
   - Consumo de ~12 a 15 MB de RAM **únicamente mientras esté encendido**.
   - Incluye temporizador de **auto-apagado por inactividad tras 30 minutos** para garantizar que no se deje RAM consumida por descuido.
   - Botón directo de apagado en la interfaz que libera la memoria al instante.

---

## 2. Invariante de Entorno Soberano (Sin Dependencia de ZCP)

Para garantizar que el Cockpit funcione tanto en `zcp` como en el futuro contenedor `astrobranding` (incluso cuando `zcp` esté apagado), la resolución de credenciales y variables opera en cascada:
1. **`process.env`**: Variables inyectadas por la plataforma Zerops a nivel de runtime.
2. **`/etc/environment`**: Variables globales del sistema operativo inyectadas durante el aprovisionamiento.
3. **`/var/www/.env`**: Variables locales del repositorio.
4. **`glamur-keys.md`**: Respaldo en Google Drive SSoT solo si existe en entorno local.

---

## 3. Las 6 Categorías Estrictas de Telemetría

### 🤖 [1/6] LLMOps & Gateways de Inferencia en Vivo (Bifrost & FreeLLMAPI)
- **Bifrost AI Gateway (`http://bifrost:8080`)**:
  - Catálogo en vivo de **258 modelos** (DeepSeek oficiales: `deepseek-chat`, `deepseek-reasoner`, `deepseek-v4-pro`, `deepseek-flash` + 253 modelos agregados de FreeLLMAPI).
  - Virtual-Keys estrictamente auténticas de la aplicación (`vk-production-main`, `vk-astrobranding-prod`, `vk-hermes-agent`, `vk-evolution-wa`) con presupuesto mensual y rate limits CEL.
  - Peticiones procesadas y tokens totales (entrada/salida).
  - **Caché Directa (Hash Exacto en SQLite/Memoria)**: 4 aciertos en vivo con latencia 0ms y costo $0.00 (30.8% de ahorro).
  - **Caché Semántica (Chromem Vector Store)**: 0 aciertos hasta procesar consultas semánticamente equivalentes.
- **FreeLLMAPI Gateway (`http://freellmapi:3001`)**:
  - Lectura en tiempo real de la base de datos física SQLite (`/var/www/localstorage/freellmapi/freellmapi.db`).
  - Total de solicitudes procesadas (éxitos vs. errores: 6 ok, 1 err).
  - Consumo de tokens (197 entrada, 1,102 salida = 1,299 tokens totales).
  - Ahorro financiero absoluto ($0.00 USD facturados).
- **Métricas Totales Combinadas**:
  - Resumen unificado de toda la inferencia del ecosistema (20 peticiones, 2,407 tokens totales, $0.0007 USD gastados).

### ☁️ [2/6] Infraestructura Zerops, Recursos Físicos & Costos SSoT
- **Consumo Real de RAM por Contenedor (cgroup v2 / Prometheus)**:
  - `zcp`: Memoria activa real en MB (Control Plane).
  - `freellmapi`: Memoria activa en MB (Node.js 24).
  - `bifrost`: Memoria activa en MB (Go 1.22).
  - `valkey`: Detección dinámica en vivo. Si el contenedor está apagado, se reporta estrictamente como `STOPPED (0 MB, $0.00 USD)`.
  - `localstorage`: Memoria activa en MB.
  - Contenedores detenidos (`astrobranding`, `hermes`, `evolution`, `database`, `nats`): marcados explícitamente en `0 MB ($0.00 de costo)`.
- **Facturación Zerops Dashboard SSoT**:
  - Reporta el gasto total proyectado oficial de la plataforma: **~$25.00 USD / mes** (~$0.83 USD/día).
  - Desglose transparente:
    - RAM activa de contenedores: `~$8.80 USD/mes`.
    - Enrutadores y balanceadores L7 HA públicos (2x réplicas): `~$14.20 USD/mes`.
    - Almacenamiento persistente dedicado (Local-Storage POSIX + S3 Object Storage): `~$2.00 USD/mes`.
- **Almacenamiento Local (POSIX)**:
  - Ocupación en `/var/www/localstorage` desglosada por servicio (`bifrostSize`, `freellmSize`, `totalUsed`).
- **Object Storage S3**:
  - Cuota real asignada por Zerops: **10 GB** (escalable dinámicamente en caliente desde la UI de Zerops sin reinicio ni corte de servicio).

### 🌐 [3/6] Browsers, Scraping & Motores de Búsqueda (Cuotas & Fechas de Corte)
Inspección en vivo mediante consultas autenticadas y lectura de cabeceras oficiales:
- **Tavily Search API**: Búsquedas consumidas vs. límite (768 / 1,000 usadas · 232 restantes · 77% consumido) | **Corte**: `Día 1 de cada mes (00:00 UTC)`.
- **Firecrawl Scraper**: Créditos consumidos vs. cuota (2 / 1,000 créditos usados · 998 restantes · 1% consumido) | **Corte**: `21 de cada mes` (Próximo: 21-Oct-2026).
- **Exa Neural Search**: **Plan Gratuito Developer** (1,000 consultas/mes gratuitas, $0.00 USD) | Consumidas: ~12 consultas · Restantes: 988 | **Corte**: `Día 1 de cada mes (00:00 UTC)`.
- **Jina AI Reader / Embeddings**: **Concesión de 1,000,000 tokens grant** (500 RPM) · 1 request (29 tok consumidos) · 999,971 tokens restantes | **Corte**: `Día 1 de cada mes`.
- **Brave Search API**: 2,000 consultas/mes gratuitas (50 RPS) | **Corte**: `Día 1 de cada mes`.

### 🔮 [4/6] APIs Astrológicas & Efemérides Científicas
- **AstrologyAPI.io**: **50 req/mes gratuitas** (30 RPM, Timing helenístico, Fagan-Bradley, ACG) | **Corte**: `Día 1 de cada mes`.
- **Astroway Engine**: **Plan Indie PRO ($5/mo, 50,000 créditos/mes)**, 30 req/min, 760 endpoints SE 2.10 | **Corte**: `Día 1 de cada mes`.
- **NASA JPL Horizons**: **9,999 / 10,000 peticiones restantes** (1,000 req/hora, efemérides DE440/DE441) | **Corte**: Ventana horaria continua.
- **FreeAstro API**: **500 consultas/día** (10 RPS, Plan Starter) | **Corte**: `Diario a las 00:00 UTC`.
- **VedAstro Jyotish**: 60 RPM | 677 calculadores atómicos védicos.
- **Kundali MCP Engine**: Ilimitado (Motor local Jyotish Shadbala, Vimshottari 5 niveles & Pramaan BPHS).

### 📨 [5/6] Cloud, Mensajería Transaccional & Edge (AWS, ZeptoMail, WhatsApp, Cloudflare)
- **Amazon Web Services (AWS)**: Integración con **SES v2** en `us-east-1` · Cuota: **50,000 emails/día** · Enviados hoy: 0 · Configuration Set `deliverability-set` · DMARC & DKIM 2048.
- **Zoho ZeptoMail**: Capacidad transaccional: **0 / 10,000 emails consumidos** (10,000 restantes en welcome pack transaccional sin caducidad mensual).
- **Resend Email Relay**: Detectada como `NO CONFIGURADA` (pendiente de aprovisionar clave real).
- **Meta WhatsApp Cloud**: Detectada como `NO CONFIGURADA` (sin WABA ID / token real activo).
- **Evolution WhatsApp API**: Microservicio Go/whatsmeow en Zerops (`http://evolution:8080`).
- **Cloudflare Edge CDN/WAF**: SSL Full Strict, Edge WAF y sincronización de DNS sin límite para `catalinaglamur.com`.

### 💳 [6/6] Pasarelas de Pago, Logística & CRM E-Commerce
- **Wompi Colombia**: Validación criptográfica SHA256 de webhooks, llaves pública/privada y secret de integridad (`ACTIVO`).
- **Frappe Cloud / ERPNext**: Conexión con `catalinaglamur.v.frappe.cloud`, API Key y facturación electrónica DIAN (`ACTIVO`).
- **ePayco, Stripe, MercadoPago, dLocal Go, MiPaquete, Carriers**: Detectadas como `NO CONFIGURADA` hasta que se suministren credenciales reales en producción, sin badges verdes ficticios.

---

## 4. Comandos de Terminal (Línea de Comandos CLI)

```bash
# 1. Reporte completo estructurado en 6 categorías
cockpit-status

# 2. Salida en formato JSON estructurado (sin colores)
cockpit-status --json

# 3. Filtros específicos por categoría
cockpit-status --llm         # Solo LLMOps (Bifrost & FreeLLMAPI)
cockpit-status --infra       # Solo Contenedores Zerops, RAM real, discos y costos
cockpit-status --browsers    # Solo Cuotas de Búsqueda y Scraping (Tavily, Firecrawl, Exa)
cockpit-status --astrology   # Solo APIs Astrológicas y Efemérides
cockpit-status --apis        # Solo Cloud, Mensajería y Edge (AWS, Zepto, WA, CF)
cockpit-status --ecommerce   # Solo Pasarelas de Pago, Logística y CRM
```

---

## 5. Control del Servidor Web (`cockpit-web`)

```bash
# Iniciar el servidor web (puerto 3050 -> Nginx 8080)
cockpit-web start

# Verificar si el servidor web está corriendo, puerto y memoria RAM
cockpit-web status

# Detener el servidor web y volver a 0 MB de memoria RAM
cockpit-web stop

# Reiniciar el servidor web tras actualizaciones
cockpit-web restart
```

---

## 6. Sincronización y Mantenimiento SSoT

- **Clonabilidad Garantizada**: Toda la infraestructura del Cockpit está sincronizada en:
  1. [`0zcp-123/scripts/setup-zcp.sh`](file:///var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/setup-zcp.sh): Despliega automáticamente `cockpit-status`, `cockpit-web` y la regla de proxy reverso `/cockpit/` en Nginx.
  2. [`unisetup.sh`](file:///var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/unisetup.sh): Garantiza que cualquier nuevo contenedor ZCP arranque con el Cockpit 100% operativo sin intervención manual.
  3. `docs/MANUAL_COCKPIT.md` y `0zcp-123/scripts/MANUAL_COCKPIT.md`: Espejados de forma idéntica en Google Drive SSoT.
