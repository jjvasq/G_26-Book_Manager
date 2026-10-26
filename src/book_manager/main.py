"""Punto de entrada principal de la aplicación Book Manager."""

from __future__ import annotations

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import (
    CARPETA_CSV,
    CARPETA_SQL,
    archivos_sql,
    base_vacia,
    cargar_datos_sql,
    migrar_datos,
)
from book_manager.repositories.repositories import crear_repositorios
from book_manager.services.services import crear_servicios
from book_manager.ui.console import Consola


def cargar_datos_iniciales(conexion: ConexionDB) -> int:
    """Carga los datos iniciales del sistema en la base.

    Se usan los archivos .sql de la migración; si todavía no existen, se
    migran los CSV del Sprint 1 (lo que además genera los .sql).

    Args:
        conexion (ConexionDB): Conexión a la base de datos.

    Returns:
        int: Cantidad de registros insertados.
    """
    if archivos_sql(CARPETA_SQL):
        return sum(cargar_datos_sql(CARPETA_SQL, conexion).values())
    return sum(migrar_datos(CARPETA_CSV, CARPETA_SQL, conexion).values())


def main(import_default_data: bool = False) -> None:
    """Inicia el sistema.

    Args:
        import_default_data (bool): Si es True, vuelve a cargar los datos
            iniciales desde los archivos .sql; solo se insertan los
            registros que faltan, sin borrar datos. Si la base no tiene
            datos cargados, la carga se hace igual.
    """
    conexion = ConexionDB()
    # Los servicios se crean primero porque configuran la auditoría, que
    # también registra la carga de datos.
    servicios = crear_servicios(crear_repositorios(conexion))
    if import_default_data or base_vacia(conexion):
        insertados = cargar_datos_iniciales(conexion)
        print(f"Carga de datos iniciales: {insertados} registros insertados.")
    Consola(servicios).ejecutar()


if __name__ == "__main__":
    main()
