# Serviphar GRC Lite (Fase 1 - Modular)

Serviphar GRC Lite es una plataforma web modular de Gobernanza, Riesgo y Cumplimiento (GRC), diseñada para el levantamiento en terreno y la gestión de evaluaciones de privacidad, seguridad y cumplimiento.

La plataforma incorpora campos configurables que pueden apoyar proyectos relacionados con protección de datos personales y marcos de referencia. La determinación de cumplimiento normativo requiere validación jurídica y técnica específica para cada organización.

---

## Módulos Disponibles en Fase 1

1. **🏠 Dashboard:** Métricas consolidadas, evaluaciones activas y gráficos de progreso.
2. **🏢 Empresas:** Catálogo y gestión de organizaciones del grupo.
3. **📁 Evaluaciones GRC (Nuevo):** Contenedor principal de proyectos de evaluación por empresa y período.
4. **📋 Tratamientos (ROPA):** Registro de tratamientos con vinculación opcional a evaluaciones.
5. **🔍 Visitas / Auditorías:** Auditorías en terreno con checklist de seguridad (15 puntos) y tipo de visita.
6. **📸 Evidencias:** Registro de enlaces a evidencias fotográficas y documentales externas.
7. **📊 Exportar Informe:** Descarga de informe consolidado Excel con 6 hojas estilizadas.

---

## ⚠️ Advertencia de Seguridad y Uso Operativo

> [!CAUTION]
> - **Uso Interno:** La plataforma está destinada exclusivamente al consultor/auditor para trabajo en terreno.
> - **Acceso Remoto:** Se accede mediante navegador web con conexión a Internet desde notebook, PC o tablet.
> - **Almacenamiento Centralizado:** No existe modo *offline*; cada operación se persiste en tiempo real en Neon PostgreSQL.
> - **Sin Acceso Externo:** La plataforma **no debe ser abierta a clientes ni terceros externos** en esta etapa.
> - **Seguridad Pendiente:** No existe sistema de login, autenticación de usuarios, roles (RBAC) ni aislamiento multiempresa validado a nivel de base de datos.
> - **Evidencias:** No se permite almacenar archivos binarios en el servidor ni usar URLs públicas para documentos confidenciales.

---

## Estructura del Código

```text
serviphar_grc_lite/
  ├── app.py                     # Router principal Streamlit
  ├── db/
  │   ├── connection.py          # Conexión y transacciones seguras
  │   ├── migrations.py          # Migraciones seguras e idempotentes (Fase 1)
  │   └── repositories/          # Repositorios CRUD por entidad
  ├── modules/                   # Módulos UI interactivos
  ├── services/                  # Servicios de lógica de negocio (Checklist)
  ├── utils/                     # Constantes, validadores y semáforos
  ├── requirements.txt           # Dependencias fijadas
  ├── runtime.txt                # python-3.11
  └── docs/
      └── IMPLEMENTACION.md      # Documentación técnica completa
```

---

## Ejecución Local

1. Asegurar dependencias instaladas:
   ```bash
   pip install -r requirements.txt
   ```
2. Configurar variable de entorno `DATABASE_URL`:
   ```bash
   # Ejemplo (reemplazar con credenciales reales en tu entorno):
   export DATABASE_URL="postgresql://usuario:contraseña@host:5432/nombre_bd?sslmode=require"
   ```
3. Iniciar Streamlit:
   ```bash
   streamlit run app.py
   ```
