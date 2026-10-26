# Book Manager

Sistema de gestión de libros desarrollado en Python para la materia 
**Seminario de Actualización I**.

## Integrantes - Grupo 26
- Frigo, Claudia Lorena
- Pappalardo, Carla Giorgina
- Vasquez, Juan José

## Sprint 3

### Objetivo

Obtener información del catálogo de la web de Cúspide para comparar los
precios con los nuestros. Y también poder auditar todas las operaciones
del sistema.

### Introducción y contexto

En este sprint se parte del Sprint 2 (persistencia en PostgreSQL con
SQLAlchemy y cotizaciones desde DolarApi) y se agrega:

Carga de los datos de la base desde los archivos `.sql` de la migración.
Un scraper hecho con Scrapy (`CuspideSpider`, con *items*, *loaders* y
*pipelines*) que busca en [Cúspide](https://cuspide.com) cada título del
catálogo y toma los 10 primeros resultados de cada búsqueda: precio, URL
de la imagen, formas de pago con su precio y descripción detallada. Solo
se buscan libros del catálogo.
La comparación del precio interno con el precio web. Antes de cada
ejecución el usuario ingresa la diferencia que dispara una alerta (en
porcentaje o en pesos) y se genera un archivo CSV de alertas.
Un reporte en Excel con libro, precio interno, precio web, diferencia y
fecha de extracción.
Un decorador de auditoría: cada operación queda registrada en la tabla
`auditoria` con la acción, la fecha y los detalles.
Las opciones de menú *Ejecutar scraping*, *Generar reporte* y *Ver
historial de auditoría*.

---

## Nueva Estructura del Proyecto

```text
├── src/
│   └── book_manager/
│       ├── database/
│       │   └── connection.py
│       ├── entities/
│       │   └── entities.py
│       ├── models/
│       │   └── models.py
│       ├── preload_data/
│       │   └── preload_data.py
│       ├── repositories/
│       │   └── repositories.py
│       ├── scraper
│       │   └── (estructura del scraper scrapy)
│       ├── services/
│       │   └── services.py
│       ├── migrations
│       │   ├── csv
│       │   └── sql
│       ├── reportes
│       │   └── (reportes excel generados)
│       ├── ui/
│       │   └── console.py
│       └── main.py
├── .env.example      (plantilla; el .env real no se versiona)
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

---

## Sprint 2

### Objetivo

Aplicar los conocimientos adquiridos en programación orientada a objetos y
consolidar las bases del manejo de bases de datos relacionales:
normalización, conexión segura y carga inicial, usando el ORM SQLAlchemy.

### Introducción y contexto

En este sprint se amplía el alcance del sistema: la aplicación deja de
persistir en archivos CSV y pasa a persistir en una base de datos
relacional mediante SQLAlchemy.

Los datos cargados durante el Sprint 1 (archivos de
`src/book_manager/migrations/csv`) se migran a tablas relacionales. Durante
la migración se generan archivos `.sql` con las sentencias de inserción en
`src/book_manager/migrations/sql`.

Además, las cotizaciones del dólar se obtienen de una API externa
(DolarApi), cuya URL se configura en el archivo `.env` junto con la cadena
de conexión a la base de datos. El sistema muestra una lista de precios
bimonetaria (en pesos y en otra moneda) y exporta los precios a CSV.

Entidades: Libro, Genero, Editorial, Moneda, TipoCotizacion, Precio, Stock y
CotizacionDolar. Cada una cuenta con su CRUD completo y su tabla en la base
de datos.

---

## Estructura del Proyecto

```text
├── src/
│   └── book_manager/
│       ├── database/
│       │   └── connection.py
│       ├── entities/
│       │   └── entities.py
│       ├── models/
│       │   └── models.py
│       ├── preload_data/
│       │   └── preload_data.py
│       ├── repositories/
│       │   └── repositories.py
│       ├── services/
│       │   └── services.py
│       ├── migrations/
│       │   ├── csv/
│       │   └── sql/
│       ├── ui/
│       │   └── console.py
│       └── main.py
├── .env.example      (plantilla; el .env real no se versiona)
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

---

### Requisitos y Configuración

#### 1. Prerrequisitos
- Python 3.10 o superior

#### 2. Entorno virtual
Se recomienda crear y activar un entorno virtual:

```bash
# Crear entorno virtual
python -m venv .venv

# Activar en Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Activar en Linux/macOS
source .venv/bin/activate
```

#### 3. Instalación de dependencias
```bash
pip install -r requirements.txt
```

#### 4. Configuración (`.env` y contraseña)

La base de datos es PostgreSQL en Supabase. El archivo `.env` contiene
datos de conexión, por eso **no se versiona** (está en `.gitignore`): en el
repositorio solo está la plantilla `.env.example`.

```bash
# en la raíz del proyecto
cp .env.example .env
```

Luego se completa `DATABASE_URL` con la URL de Supabase
(Connect > ORM > DIRECT_URL), dejando el marcador `[YOUR-PASSWORD]`:

```bash
DATABASE_URL=postgresql://postgres.<id-proyecto>:[YOUR-PASSWORD]@<host>.pooler.supabase.com:5432/postgres
API_URL=https://dolarapi.com/v1/dolares
```

La contraseña nunca se escribe en archivos: se carga como variable de
entorno `SUPABASE_DB_PASSWORD`.

```bash
# Linux / macOS
export SUPABASE_DB_PASSWORD="la_contraseña"
# Windows (PowerShell)
$env:SUPABASE_DB_PASSWORD = "la_contraseña"
```

En Colab se usan dos secrets: `DATABASE_URL` (la URL de conexión) y
`SUPABASE_DB_PASSWORD`. El notebook arma el `.env` a partir de
`.env.example` con el valor del secret `DATABASE_URL` y carga la
contraseña en la variable de entorno.

#### 5. Ejecución

Desde una consola, en el directorio `src`:

```bash
# inicia el sistema (si la base está vacía la carga desde los .sql de
# migrations/sql; si todavía no hay .sql, migra los CSV del Sprint 1)
python -m book_manager.main

# migra los CSV del Sprint 1 y genera los .sql (es repetible: solo
# inserta los registros que faltan y no borra datos)
python -m book_manager.migrations.migrations

# ATENCIÓN: borra la base y la carga con los datos de ejemplo
python -m book_manager.preload_data.preload_data
```

Desde un notebook:

```python
from book_manager.main import main

# usa la base existente (la migra si está vacía)
main(import_default_data=False)

# vuelve a cargar los datos desde los .sql (solo agrega lo que falta)
main(import_default_data=True)

# carga directa desde los archivos .sql
from book_manager.migrations.migrations import CARPETA_SQL, cargar_datos_sql
cargar_datos_sql(CARPETA_SQL)
```

Los precios exportados desde el menú *Lista de precios* se guardan en
`src/book_manager/exports`.

#### 6. Precios de la competencia y auditoría (Sprint 3)

En el menú principal:

- **Ejecutar scraping**: pide la diferencia de precio que dispara una alerta
y el tipo de moneda para los precios internos en otra moneda, busca los libros
en cuspide.com, muestra la comparación y genera el archivo CSV.
- **Generar reporte**: genera un archivo excel con la última ejecución del
scraping.
- Al terminar el scraping y al generar el reporte, el sistema pregunta si
  se quiere descargar el archivo: en Google Colab se descarga desde el
  navegador, fuera de Colab se informa en qué carpeta quedó.
- **Ver historial de auditoría**: muestra los registros de la tabla
  `auditoria` (acción, fecha y detalles) del más reciente al más antiguo.
