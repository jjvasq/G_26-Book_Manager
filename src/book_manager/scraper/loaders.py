"""Item loaders y procesadores de los datos obtenidos de Cúspide."""

from __future__ import annotations

import re
from typing import Optional

from itemloaders.processors import Identity, Join, MapCompose, TakeFirst
from scrapy.loader import ItemLoader

from book_manager.scraper.items import LibroWebItem


def limpiar_texto(valor: str) -> Optional[str]:
    """Quita los espacios repetidos y los de los extremos de un texto.

    Args:
        valor (str): Texto extraído de la página.

    Returns:
        Optional[str]: Texto limpio, o None si queda vacío (MapCompose
            descarta los valores None).
    """
    texto = " ".join(str(valor).split())
    return texto or None


def texto_a_precio(valor: str) -> Optional[float]:
    """Convierte un precio con formato argentino en un número.

    Ejemplos: "$ 52.900,00" -> 52900.0 y "34,35" -> 34.35.

    Args:
        valor (str): Precio como texto.

    Returns:
        Optional[float]: El precio, o None si el texto no tiene un número.
    """
    numero = re.sub(r"[^\d,.]", "", valor)
    if not re.search(r"\d", numero):
        return None
    numero = numero.replace(".", "").replace(",", ".")
    try:
        return float(numero)
    except ValueError:
        return None


def limpiar_isbn(valor: str) -> Optional[str]:
    """Deja solo los dígitos (y la X final del ISBN-10) de un ISBN.

    Args:
        valor (str): ISBN como texto.

    Returns:
        Optional[str]: ISBN normalizado, o None si queda vacío.
    """
    isbn = re.sub(r"[^\dXx]", "", valor).upper()
    return isbn or None


def quitar_vineta(valor: str) -> Optional[str]:
    """Quita la viñeta ("> ") con la que el sitio lista los medios de pago.

    Args:
        valor (str): Texto del medio de pago.

    Returns:
        Optional[str]: Texto sin la viñeta, o None si queda vacío.
    """
    texto = valor.lstrip(">•- ").strip()
    return texto or None


class LibroWebLoader(ItemLoader):
    """Loader del item LibroWebItem.

    Por defecto limpia los textos y toma el primer valor no vacío. Los
    precios se convierten a número, los medios de pago se guardan como
    lista y la descripción une todos sus párrafos.
    """

    default_item_class = LibroWebItem
    default_input_processor = MapCompose(limpiar_texto)
    default_output_processor = TakeFirst()

    libro_id_in = MapCompose(int)
    posicion_in = MapCompose(int)
    isbn_in = MapCompose(limpiar_texto, limpiar_isbn)
    precio_in = MapCompose(limpiar_texto, texto_a_precio)
    precio_usd_in = MapCompose(limpiar_texto, texto_a_precio)
    medios_pago_argentina_in = MapCompose(limpiar_texto, quitar_vineta)
    medios_pago_argentina_out = Identity()
    medios_pago_internacionales_in = MapCompose(limpiar_texto, quitar_vineta)
    medios_pago_internacionales_out = Identity()
    descripcion_out = Join(" ")
