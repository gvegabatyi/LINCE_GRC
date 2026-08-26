# Serviphar GRC Lite - Documentación de Implementación

## Índice
1. [Resumen del Proyecto](#resumen-del-proyecto)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Tecnologías Utilizadas](#tecnologías-utilizadas)
4. [Configuración del Entorno](#configuración-del-entorno)
5. [Integración GitHub + Railway](#integración-github--railway)
6. [Base de Datos Neon PostgreSQL](#base-de-datos-neon-postgresql)
7. [Despliegue y Ejecución](#despliegue-y-ejecución)
8. [Módulos de la Aplicación](#módulos-de-la-aplicación)
9. [Solución de Problemas](#solución-de-problemas)
10. [Comandos Útiles](#comandos-útiles)
11. [Recursos Adicionales](#recursos-adicionales)

---

## Resumen del Proyecto
**Serviphar GRC Lite** es una aplicación web de gestión de cumplimiento normativo (GRC - Governance, Risk & Compliance) diseñada para PYMEs y adaptada a la Ley 21.719 / GDPR. Permite registrar empresas, tratamientos de datos (ROPA), visitas de auditoría y exportar informes a Excel.

- **URL de Producción:** [https://serviphar-grc-lite-production.up.railway.app/](https://serviphar-grc-lite-production.up.railway.app/)
- **Repositorio:** [https://github.com/gvegabatyi/serviphar-grc-lite](https://github.com/gvegabatyi/serviphar-grc-lite)

---

## Arquitectura del Sistema

```text
┌─────────────────┐
│   Usuario       │
│   (Navegador)   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│   Railway       │
│   (Hosting)     │
│   Puerto: 8501  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Streamlit     │
│   (app.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Neon          │
│   (PostgreSQL)  │
└─────────────────┘
```

### Flujo de Datos:
1. El usuario accede vía navegador a la URL de Railway.
2. Railway ejecuta el contenedor con la app de Streamlit.
3. Streamlit procesa las interacciones del usuario en tiempo real.
4. Los datos se guardan y consultan directamente en la base de datos **Neon PostgreSQL**.

---

## Tecnologías Utilizadas

### Backend & Frontend
| Tecnología | Versión | Propósito |
| :--- | :--- | :--- |
| **Python** | 3.11 | Lenguaje principal |
| **Streamlit** | 1.32.0 | Framework web interactivo |
| **Pandas** | 2.0.3 | Manipulación y estructuración de datos |
| **psycopg2-binary** | 2.9.9 | Conector y consultas PostgreSQL |
| **openpyxl** | 3.1.2 | Generación y exportación a Excel |

### Infraestructura
| Servicio | Propósito |
| :--- | :--- |
| **GitHub** | Repositorio y control de versiones |
| **Railway** | Hosting y despliegue continuo automático (CI/CD) |
| **Neon** | Base de datos PostgreSQL serverless en la nube |
| **Railpack / Nixpacks** | Builder de Railway para Python |

---

## Configuración del Entorno

### Estructura del Proyecto
```text
serviphar-grc-lite/
├── docs/
│   └── IMPLEMENTACION.md     # Documentación completa del proyecto
├── app.py                    # Aplicación principal (Streamlit + PostgreSQL)
├── requirements.txt          # Dependencias de Python
├── runtime.txt               # Versión de Python fijada (python-3.11)
├── railpack-plan.json        # Configuración opcional de build de Railway
└── README.md                 # Guía general de uso
```

### Archivos Clave

#### 1. `requirements.txt`
```text
streamlit==1.32.0
pandas==2.0.3
psycopg2-binary==2.9.9
openpyxl==3.1.2
```

#### 2. `runtime.txt`
```text
python-3.11
```

#### 3. `railpack-plan.json`
```json
{
  "$schema": "https://railpack.com/schema/railpack-plan.json",
  "setup": {
    "packages": {
      "python": "3.11"
    }
  }
}
```

---

## Integración GitHub + Railway

### Paso a Paso de la Integración

1. **Repositorio GitHub**:
   - URL: `https://github.com/gvegabatyi/serviphar-grc-lite`
   - Rama principal: `main`

2. **Conexión con Railway**:
   - En Railway, crear un nuevo proyecto.
   - Seleccionar **"Deploy from GitHub repo"**.
   - Elegir el repositorio `serviphar-grc-lite`.
   - Railway detecta automáticamente el proyecto Python.

3. **Configuración de Auto-Deploy**:
   - Railway monitorea la rama `main`.
   - Cada `git push` a `main` desencadena un build y despliegue automático.

4. **Flujo de Trabajo**:
```text
1. Desarrollador hace cambios en código local
2. git add . && git commit -m "mensaje"
3. git push origin main
4. GitHub recibe el push
5. Railway detecta el cambio
6. Railway hace build automático
7. Railway despliega la nueva versión
8. URL de producción actualizada
```

---

## Base de Datos Neon PostgreSQL

### Configuración
1. **Crear Base de Datos en Neon**:
   - Ir a [https://neon.tech](https://neon.tech)
   - Crear proyecto `serviphar-grc-lite`.
   - Copiar la cadena de conexión (`DATABASE_URL`).

2. **Formato de `DATABASE_URL`**:
```text
postgresql://usuario:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
```

3. **Variables de Entorno en Railway**:
   - En Railway → Variables:
     - `DATABASE_URL`: URL completa de conexión provista por Neon.

4. **Esquema de Base de Datos**:
La aplicación inicializa automáticamente las tablas al arrancar si no existen:

```sql
-- Tabla: empresas
CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    rut TEXT,
    estado TEXT DEFAULT 'activa'
);

-- Tabla: tratamientos (ROPA)
CREATE TABLE IF NOT EXISTS tratamientos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    nombre TEXT,
    finalidad TEXT,
    datos TEXT,
    titulares TEXT,
    base_licitud TEXT,
    riesgo TEXT
);

-- Tabla: visitas
CREATE TABLE IF NOT EXISTS visitas (
    id SERIAL PRIMARY KEY,
    tipo TEXT,
    empresa TEXT,
    fecha DATE,
    participantes TEXT,
    hallazgos TEXT
);
```

---

## Despliegue y Ejecución

### Opción 1: Producción (Railway)
- **URL:** [https://serviphar-grc-lite-production.up.railway.app/](https://serviphar-grc-lite-production.up.railway.app/)
- **Puerto:** `8501`
- **Comando de Inicio en Railway:**
```bash
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

### Opción 2: Local (Desarrollo)

1. **Clonar repositorio:**
```bash
git clone https://github.com/gvegabatyi/serviphar-grc-lite.git
cd serviphar-grc-lite
```

2. **Crear entorno virtual e instalar dependencias:**
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

3. **Configurar variable de entorno:**
```powershell
# En PowerShell:
$env:DATABASE_URL="postgresql://usuario:password@host/dbname?sslmode=require"

# En Bash / Linux / Mac:
export DATABASE_URL="postgresql://usuario:password@host/dbname?sslmode=require"
```

4. **Ejecutar la app:**
```bash
streamlit run app.py
```
- Acceso: `http://localhost:8501`

---

## Módulos de la Aplicación

1. **Empresas**:
   - Registro de empresas del grupo (Nombre y RUT).
   - Visualización tabular en tiempo real.

2. **Tratamientos (ROPA)**:
   - Selección de empresa asociada.
   - Registro de finalidad, tipos de datos, categorías de titulares, base de licitud y nivel de riesgo (bajo, medio, alto, crítico).
   - Listado consolidado vinculando la empresa por su nombre.

3. **Visitas y Entrevistas**:
   - Registro ágil en terreno de visitas (bodega, farmacia, RRHH, TI, operaciones, etc.).
   - Captura de fecha, participantes y hallazgos principales.

4. **Exportar**:
   - Generación instantánea y botón de descarga directa de `serviphar_grc_lite_export.xlsx` con una pestaña por cada tabla (`empresas`, `tratamientos`, `visitas`).

---

## Solución de Problemas

### 1. Error 502 (Bad Gateway)
- **Causa:** La aplicación no está escuchando en el puerto esperado.
- **Solución:** Verificar que el comando de inicio en Railway sea:
  `streamlit run app.py --server.port=8501 --server.address=0.0.0.0` y que el puerto en Railway Networking sea `8501`.

### 2. Error de Conexión a Base de Datos
- **Causa:** `DATABASE_URL` no está definida o formato incorrecto.
- **Solución:**
  - En Railway → Variables, verificar que `DATABASE_URL` contenga la cadena de Neon con `?sslmode=require`.
  - Asegurarse de que el string empiece por `postgresql://` (la app normaliza automáticamente si viene con `postgres://`).

### 3. Error de Dependencias / Compilación
- **Causa:** Incompatibilidad de paquetes compilados.
- **Solución:** Asegurar el uso de `pandas==2.0.3`, `psycopg2-binary==2.9.9` y `runtime.txt` con `python-3.11`.

---

## Comandos Útiles

### Git & GitHub
```bash
git status
git add .
git commit -m "Añadir documentación de implementación"
git push origin main
```

### Base de Datos (psql)
```bash
# Conectar desde terminal
psql "postgresql://usuario:password@ep-xxx.neon.tech/dbname?sslmode=require"

# Listar tablas
\dt

# Consultar empresas
SELECT * FROM empresas;
```

---

## Recursos Adicionales

- **Streamlit Docs:** [https://docs.streamlit.io](https://docs.streamlit.io)
- **Railway Docs:** [https://docs.railway.com](https://docs.railway.com)
- **Neon Docs:** [https://neon.tech/docs](https://neon.tech/docs)
- **GitHub del Proyecto:** [https://github.com/gvegabatyi/serviphar-grc-lite](https://github.com/gvegabatyi/serviphar-grc-lite)

---
*Última actualización: 26 de agosto de 2026*  
*Versión: 1.0.0*  
*Autor: Gonzalo Vega Batyi*
