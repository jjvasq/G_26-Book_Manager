"""Punto de entrada principal de la aplicación Book Manager."""

from __future__ import annotations

from book_manager.preload_data.preload_data import hay_datos, precargar_datos
from book_manager.repositories.repositories import crear_repositorios
from book_manager.services.services import crear_servicios
from book_manager.ui.console import Consola


def main(import_default_data: bool = False) -> None:
    """Inicia el sistema.

    Args:
        import_default_data (bool): Si es True, regenera los CSV con los
            datos de ejemplo antes de iniciar. Si no hay datos cargados,
            la precarga se hace igual.
    """
    if import_default_data or not hay_datos():
        precargar_datos()
        print("Datos de ejemplo precargados.")
    servicios = crear_servicios(crear_repositorios())
    Consola(servicios).ejecutar()


if __name__ == "__main__":
    main()
