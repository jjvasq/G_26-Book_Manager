"""Punto de entrada principal de la aplicación Book Manager."""

from __future__ import annotations

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import (
    CARPETA_CSV,
    CARPETA_SQL,
    base_vacia,
    migrar_datos,
)
from book_manager.repositories.repositories import crear_repositorios
from book_manager.services.services import crear_servicios
from book_manager.ui.console import Consola


def main(import_default_data: bool = False) -> None:
    """Inicia el sistema.

    Args:
        import_default_data (bool): Si es True, vuelve a migrar a la base
            de datos los datos del Sprint 1 (archivos CSV). Si la base no
            tiene datos cargados, la migración se hace igual.
    """
    conexion = ConexionDB()
    if import_default_data or base_vacia(conexion):
        resumen = migrar_datos(CARPETA_CSV, CARPETA_SQL, conexion)
        print(
            f"Datos del Sprint 1 migrados a {conexion.url} "
            f"({sum(resumen.values())} registros)."
        )
    servicios = crear_servicios(crear_repositorios())
    Consola(servicios).ejecutar()


if __name__ == "__main__":
    main()
