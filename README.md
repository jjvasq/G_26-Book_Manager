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
├── .env
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

#### 4. Ejecución

Desde un consola:

ir al directorio `src`:
```bash
# usa los datos existentes
python -m book_manager.main

# precarga los datos de ejemplo
python -m book_manager.preload_data.preload_data
```

Desde un notebook:

```python
from book_manager.main import main

# usa los datos existentes
main(import_default_data=False)

# regenera los datos de ejemplo
main(import_default_data=True)
```
