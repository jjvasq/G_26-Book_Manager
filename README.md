# Book Manager

Sistema de gestión de libros desarrollado en Python para la materia 
**Seminario de Actualización I**.

## Integrantes - Grupo 26
- Frigo, Claudia Lorena
- Pappalardo, Carla Giorgina
- Vasquez, Juan José

## Sprint 1

### Objetivo

Aplicar los conocimientos adquiridos en programación orientada a objetos y
en almacenamiento de datos en archivos para su persistencia.

### Introducción y contexto

Una librería con venta al público necesita modernizar su sistema de gestión
de inventario de libros. Debido a la fluctuación en los costos de importación
de material bibliográfico, el sistema debe gestionar precios en diferentes
monedas y seguir de cerca la cotización del dólar para actualizar sus valores.

Se desarrolla una aplicación de consola (CLI) en Python que permite gestionar
el inventario, cotizar los libros según el valor del dólar y, en próximos
sprints, comparar precios con la competencia web (sitio de referencia:
Cúspide).

Entidades: Libro, Genero, Editorial, Moneda, TipoCotizacion, Precio, Stock y
CotizacionDolar. Cada una cuenta con su CRUD completo y se persiste en
archivos CSV dentro de `src/book_manager/migrations/csv`.

---

## Estructura del Proyecto

```text
├── src/
│   └── book_manager/
│       ├── entities/
│       │   └── entities.py
│       ├── preload_data/
│       │   └── preload_data.py
│       ├── repositories/
│       │   └── repositories.py
│       ├── services/
│       │   └── services.py
│       ├── migrations/
│       │   └── csv/
│       ├── ui/
│       │   └── console.py
│       └── main.py
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
