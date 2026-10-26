"""Decorador de auditoría de las operaciones del sistema.

Cada función o método decorado con @auditar() deja un registro en la
tabla auditoria con la acción, la fecha y los detalles (parámetros y
resultado, o el error si la operación falló). El registro lo hace el
ServicioAuditoria, que se configura una sola vez al crear los servicios
con configurar_auditoria.
"""

from __future__ import annotations

import datetime
import functools
import inspect
import warnings
from typing import Any, Callable, Optional, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])

# Función que guarda un registro de auditoría: recibe la acción, los
# detalles y el momento en que empezó la operación.
Registrador = Callable[[str, str, datetime.datetime], Any]

# Largo máximo de los detalles y de cada valor descripto.
LARGO_MAXIMO_DETALLES = 2000
LARGO_MAXIMO_VALOR = 200

_registrador: Optional[Registrador] = None


def configurar_auditoria(registrador: Optional[Registrador]) -> None:
    """Indica la función que guarda los registros de auditoría.

    Args:
        registrador (Optional[Registrador]): Función que recibe la
            acción, los detalles y la fecha. Con None se desactiva la
            auditoría.
    """
    global _registrador
    _registrador = registrador


def describir(valor: Any) -> str:
    """Describe un valor en pocas palabras para el detalle de auditoría.

    Las entidades, textos, números y fechas se muestran con str; las
    colecciones, con su cantidad de elementos; el resto de los objetos,
    con el nombre de su clase.

    Args:
        valor (Any): Valor a describir.

    Returns:
        str: Descripción del valor.
    """
    if valor is None:
        return "-"
    if isinstance(valor, (list, tuple, set, dict)):
        return f"{len(valor)} elemento(s)"
    if isinstance(valor, (str, int, float, datetime.date)) or (
        type(valor).__str__ is not object.__str__
    ):
        texto = str(valor)
    else:
        texto = type(valor).__name__
    if len(texto) > LARGO_MAXIMO_VALOR:
        texto = texto[:LARGO_MAXIMO_VALOR - 3] + "..."
    return texto


def _nombre_accion(
    funcion: Callable[..., Any], args: tuple, accion: Optional[str]
) -> str:
    """Arma el nombre de la acción auditada.

    Para los métodos de un servicio se usa "<Entidad>.<método>" según la
    clase del objeto. Para las funciones, su nombre.

    Args:
        funcion (Callable[..., Any]): Función decorada.
        args (tuple): Argumentos posicionales de la llamada.
        accion (Optional[str]): Nombre indicado en el decorador.

    Returns:
        str: Nombre de la acción.
    """
    if accion:
        return accion
    if "." in funcion.__qualname__ and args:
        clase = type(args[0]).__name__.removeprefix("Servicio")
        return f"{clase}.{funcion.__name__}"
    return funcion.__name__


def _describir_parametros(
    funcion: Callable[..., Any], args: tuple, kwargs: dict
) -> str:
    """Describe los parámetros de una llamada (sin self).

    Args:
        funcion (Callable[..., Any]): Función decorada.
        args (tuple): Argumentos posicionales.
        kwargs (dict): Argumentos con nombre.

    Returns:
        str: Parámetros como "nombre=valor", separados por coma.
    """
    try:
        enlazados = inspect.signature(funcion).bind(*args, **kwargs)
    except TypeError:
        return ", ".join(describir(valor) for valor in args)
    return ", ".join(
        f"{nombre}={describir(valor)}"
        for nombre, valor in enlazados.arguments.items()
        if nombre not in ("self", "cls")
    ) or "-"


def _registrar(
    accion: str, detalles: str, fecha: datetime.datetime
) -> None:
    """Guarda el registro de auditoría, si la auditoría está configurada.

    Un problema al guardar la auditoría no hace fallar la operación que
    ya se realizó: se informa con una advertencia.

    Args:
        accion (str): Acción realizada.
        detalles (str): Detalles de la operación.
        fecha (datetime.datetime): Momento en que empezó la operación.
    """
    if _registrador is None:
        return
    try:
        _registrador(accion, detalles[:LARGO_MAXIMO_DETALLES], fecha)
    except Exception as error:  
        warnings.warn(
            f"No se pudo registrar la auditoría de {accion}: {error}",
            RuntimeWarning,
            stacklevel=3,
        )


def auditar(accion: Optional[str] = None) -> Callable[[F], F]:
    """Decorador que audita cada ejecución de una función o método.

    Args:
        accion (Optional[str]): Nombre de la acción. Si es None se usa
            "<Entidad>.<método>" (o el nombre de la función).

    Returns:
        Callable[[F], F]: Decorador.
    """
    def decorador(funcion: F) -> F:
        @functools.wraps(funcion)
        def envoltura(*args: Any, **kwargs: Any) -> Any:
            fecha = datetime.datetime.now().replace(microsecond=0)
            nombre = _nombre_accion(funcion, args, accion)
            parametros = _describir_parametros(funcion, args, kwargs)
            try:
                resultado = funcion(*args, **kwargs)
            except Exception as error:
                _registrar(nombre, (
                    f"ERROR {type(error).__name__}: {error} | "
                    f"parámetros: {parametros}"
                ), fecha)
                raise
            _registrar(nombre, (
                f"OK | parámetros: {parametros} | "
                f"resultado: {describir(resultado)}"
            ), fecha)
            return resultado
        return cast(F, envoltura)
    return decorador
