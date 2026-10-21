# Book Manager

Sistema de gestión de libros desarrollado en Python para la materia 
**Seminario de Actualización I**.

## Integrantes - Grupo 26
- Frigo, Claudia Lorena
- Pappalardo, Carla Giorgina
- Vasquez, Juan José

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
# inicia el sistema (si la base está vacía migra los datos del Sprint 1)
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

# vuelve a ejecutar la migración (solo agrega los registros que faltan)
main(import_default_data=True)
```

Los precios exportados desde el menú *Lista de precios* se guardan en
`src/book_manager/exports`.
