# Serviphar GRC Lite (PostgreSQL Edition)

App web portable simplificada para registrar y gestionar en terreno el proyecto de protección de datos (Ley 21.719), conectada a una base de datos centralizada **PostgreSQL**:
- **Empresas del grupo** (nombre y RUT).
- **Tratamientos (ROPA)** (finalidad, datos, titulares, licitud, riesgo).
- **Visitas y entrevistas** (bodega, farmacia, RRHH, TI, operaciones, hallazgos).
- **Exportar a Excel** (.xlsx con hojas para empresas, tratamientos y visitas).

## Estructura de Archivos

```text
serviphar_grc_lite/
  ├── app.py
  ├── requirements.txt
  └── README.md
```

## Requisitos y Dependencias

Las dependencias se encuentran en `requirements.txt`:
```text
streamlit==1.32.0
pandas==2.0.3
openpyxl==3.1.2
psycopg2-binary==2.9.9
```

## Configuración de Base de Datos

La aplicación requiere la variable de entorno `DATABASE_URL` con el string de conexión de PostgreSQL:
```bash
# Ejemplo:
DATABASE_URL="postgresql://usuario:contraseña@host:5432/nombre_bd"
```

## Cómo ejecutar en Google AI Studio / Antigravity

1. Asegurar que las dependencias estén instaladas:
   ```bash
   pip install -r requirements.txt
   ```
2. Configurar la variable `DATABASE_URL`.
3. Ejecutar la aplicación Streamlit:
   ```bash
   streamlit run app.py
   ```
4. Abrir la URL en tu PC o tablet.

## Módulos de la Aplicación

1. **Empresas**: Registro y visualización de empresas del grupo.
2. **Tratamientos (ROPA)**: Registro de tratamientos vinculados a cada empresa.
3. **Visitas**: Registro ágil en terreno de entrevistas y visitas.
4. **Exportar**: Descarga directa de `serviphar_grc_lite_export.xlsx`.
