"""Migración de los datos del Sprint 1 (archivos CSV) a la base de datos."""

from __future__ import annotations

import datetime
import os
from typing import Dict, List, Optional, Tuple, Type

from sqlalchemy import Table, func, insert, select

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import texto_a_fecha
from book_manager.models.models import (
    Base,
    CotizacionDolarModel,
    EditorialModel,
    GeneroModel,
    LibroModel,
    MonedaModel,
    PrecioModel,
    StockModel,
    TipoCotizacionModel,
    crear_tablas,
    eliminar_tablas,
)
from book_manager.repositories.repositories import ArchivoCSV

CARPETA_MIGRACIONES = os.path.dirname(os.path.abspath(__file__))
CARPETA_CSV = os.path.join(CARPETA_MIGRACIONES, "csv")
CARPETA_SQL = os.path.join(CARPETA_MIGRACIONES, "sql")

# Archivo CSV de origen y modelo destino, en el orden en que deben
# insertarse para respetar las claves foráneas.
ORDEN_MIGRACION: List[Tuple[str, Type[Base]]] = [
    ("generos.csv", GeneroModel),
    ("editoriales.csv", EditorialModel),
    ("monedas.csv", MonedaModel),
    ("tipos_cotizacion.csv", TipoCotizacionModel),
    ("libros.csv", LibroModel),
    ("precios.csv", PrecioModel),
    ("stock.csv", StockModel),
    ("cotizaciones_dolar.csv", CotizacionDolarModel),
]


def _convertir_valor(tabla: Table, columna: str, texto: str) -> object:
    """Convierte un valor leído del CSV al tipo de la columna destino.

    Args:
        tabla (Table): Tabla destino.
        columna (str): Nombre de la columna.
        texto (str): Valor leído del CSV.

    Returns:
        object: Valor convertido (int, float, str o fecha).
    """
    tipo = tabla.columns[columna].type.python_type
    if tipo is datetime.date:
        return texto_a_fecha(texto)
    if tipo is int:
        return int(texto)
    if tipo is float:
        return float(texto)
    return texto


def _leer_filas(carpeta_csvs: str, archivo: str, tabla: Table) -> List[Dict]:
    """Lee un CSV y convierte sus filas a valores para la tabla.

    Solo se toman las columnas que existen en la tabla. Si la fila no
    tiene la columna `estado` se la considera activa.

    Args:
        carpeta_csvs (str): Carpeta de los archivos CSV.
        archivo (str): Nombre del archivo CSV.
        tabla (Table): Tabla destino.

    Returns:
        List[Dict]: Filas con los valores ya convertidos.
    """
    columnas = [columna.name for columna in tabla.columns]
    filas = []
    for fila in ArchivoCSV(archivo, columnas, carpeta_csvs).leer():
        fila.setdefault("estado", "1")
        filas.append({
            columna: _convertir_valor(tabla, columna, fila[columna])
            for columna in columnas
            if columna in fila
        })
    return filas


def _generar_sentencias(
    conexion: ConexionDB, tabla: Table, filas: List[Dict]
) -> List[str]:
    """Arma las sentencias INSERT (en SQL de texto) de cada fila.

    Args:
        conexion (ConexionDB): Conexión, para usar el dialecto de la base.
        tabla (Table): Tabla destino.
        filas (List[Dict]): Filas a insertar.

    Returns:
        List[str]: Una sentencia INSERT por fila.
    """
    return [
        str(
            insert(tabla).values(**fila).compile(
                dialect=conexion.engine.dialect,
                compile_kwargs={"literal_binds": True},
            )
        ).replace("\n", " ")
        for fila in filas
    ]


def _escribir_sql(
    carpeta_sqls: str, numero: int, tabla: Table, sentencias: List[str]
) -> str:
    """Guarda las sentencias en un archivo .sql.

    Args:
        carpeta_sqls (str): Carpeta donde se guardan los .sql.
        numero (int): Orden de ejecución, para el nombre del archivo.
        tabla (Table): Tabla a la que corresponden las sentencias.
        sentencias (List[str]): Sentencias INSERT.

    Returns:
        str: Ruta del archivo generado.
    """
    os.makedirs(carpeta_sqls, exist_ok=True)
    ruta = os.path.join(carpeta_sqls, f"{numero:02d}_{tabla.name}.sql")
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(f"-- Migración de datos: tabla {tabla.name}\n")
        archivo.write(f"-- Registros: {len(sentencias)}\n\n")
        for sentencia in sentencias:
            archivo.write(sentencia + ";\n")
    return ruta


def _ajustar_secuencias(conexion: ConexionDB) -> None:
    """Actualiza los autoincrementales de PostgreSQL tras la migración.

    Como la migración inserta los ID originales, en PostgreSQL hay que
    mover cada secuencia al mayor ID cargado para que las altas nuevas
    no repitan valores.

    Args:
        conexion (ConexionDB): Conexión a la base de datos.
    """
    if conexion.engine.dialect.name != "postgresql":
        return
    with conexion.transaccion() as sesion:
        for _, modelo in ORDEN_MIGRACION:
            tabla = modelo.__table__
            if "id" not in tabla.columns:
                continue
            sesion.connection().exec_driver_sql(
                f"SELECT setval(pg_get_serial_sequence('{tabla.name}', 'id'),"
                f" COALESCE(MAX(id), 1)) FROM {tabla.name}"
            )


def migrar_datos(
    carpeta_csvs: str,
    carpeta_sqls: str,
    conexion: Optional[ConexionDB] = None,
) -> Dict[str, int]:
    """Función encargada de la migración de datos de csv a sql.

    Se encarga de leer los archivos csv y crear los archivos sql
    para la inserción en la base de datos. Las tablas se crean de
    nuevo y las sentencias de los archivos .sql se ejecutan en una
    única transacción: si alguna falla, no se guarda nada.

    Args:
        carpeta_csvs (str): Carpeta donde se encuentran los archivos csv de
            origen.
        carpeta_sqls (str): Carpeta donde se deben guardar los archivos sql
            generados.
        conexion (Optional[ConexionDB]): Conexión a la base de datos. Si
            es None se crea una con la configuración del .env.

    Returns:
        Dict[str, int]: Cantidad de registros migrados por tabla.
    """
    conexion = conexion or ConexionDB()
    eliminar_tablas(conexion)
    crear_tablas(conexion)
    resumen: Dict[str, int] = {}
    with conexion.transaccion() as sesion:
        for numero, (archivo, modelo) in enumerate(ORDEN_MIGRACION, start=1):
            tabla = modelo.__table__
            filas = _leer_filas(carpeta_csvs, archivo, tabla)
            sentencias = _generar_sentencias(conexion, tabla, filas)
            _escribir_sql(carpeta_sqls, numero, tabla, sentencias)
            for sentencia in sentencias:
                sesion.connection().exec_driver_sql(sentencia)
            resumen[tabla.name] = len(sentencias)
    _ajustar_secuencias(conexion)
    return resumen


def base_vacia(conexion: ConexionDB) -> bool:
    """Indica si la base todavía no tiene libros cargados.

    Args:
        conexion (ConexionDB): Conexión a la base de datos.

    Returns:
        bool: True si la tabla de libros no tiene registros.
    """
    crear_tablas(conexion)
    with conexion.transaccion() as sesion:
        cantidad = sesion.scalar(select(func.count()).select_from(LibroModel))
    return not cantidad


if __name__ == "__main__":
    for nombre, cantidad in migrar_datos(CARPETA_CSV, CARPETA_SQL).items():
        print(f"{nombre:<20} {cantidad:>4} registros")
