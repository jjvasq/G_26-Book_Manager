"""Excepciones personalizadas de Book Manager.

Todas heredan de `BookManagerError`, así se pueden capturar juntas. Además
heredan de `ValueError` o `RuntimeError` según el tipo de problema, para
que el código que ya capturaba esas excepciones siga funcionando.
"""

from __future__ import annotations


class BookManagerError(Exception):
    """Excepción base de todos los errores propios del sistema."""

    def __init__(self, mensaje: str) -> None:
        """Constructor.

        Args:
            mensaje (str): Descripción del error para mostrar al usuario.
        """
        super().__init__(mensaje)
        self.mensaje: str = mensaje


class DatoInvalidoError(BookManagerError, ValueError):
    """Un dato no cumple con las validaciones de la entidad."""


class RegistroNoEncontradoError(BookManagerError, ValueError):
    """El registro buscado no existe en la base de datos."""


class RegistroDuplicadoError(BookManagerError, ValueError):
    """Ya existe un registro con el mismo identificador o valor único."""


class RegistroEnUsoError(BookManagerError, ValueError):
    """No se puede eliminar un registro porque otros dependen de él."""


class StockInsuficienteError(BookManagerError, ValueError):
    """Se intenta retirar más unidades de las disponibles."""

    def __init__(self, disponible: int, solicitado: int) -> None:
        """Constructor.

        Args:
            disponible (int): Unidades que hay en stock.
            solicitado (int): Unidades que se quisieron retirar.
        """
        super().__init__(
            f"Stock insuficiente: hay {disponible} unidades "
            f"y se pidieron {solicitado}."
        )
        self.disponible: int = disponible
        self.solicitado: int = solicitado


class ConfiguracionError(BookManagerError, RuntimeError):
    """Falta una variable de entorno o del archivo .env."""


class ApiCotizacionesError(BookManagerError, RuntimeError):
    """No se pudieron obtener las cotizaciones de la API externa."""
